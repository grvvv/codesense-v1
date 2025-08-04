import os
import logging
import asyncio
import aiohttp
import hashlib
import psutil
from .files import read_file
from .prompts import create_enhanced_prompt
from .config import get_qa_chain, MAX_TOKENS
from .extract import extract_relevant_info
import logging
logger = logging.getLogger(__name__)

def analyze_code_chunk(chunk, file_name, file_extension, scan_id, triggered_by, file_content):
    """Analyze a single code chunk for vulnerabilities."""
    qa_chain = get_qa_chain()
    if not qa_chain:
        raise RuntimeError("QA chain not initialized. Call initialize_knowledge_base() first.")
    
    findings = []
    try:
        prompt = create_enhanced_prompt(chunk, file_name, file_extension)
        result = qa_chain.invoke({"query": prompt})

        if result and "result" in result:
            output = result["result"]
            findings = extract_relevant_info(output, file_name, scan_id, triggered_by, file_content)
            
            # Log source documents for debugging
            if "source_documents" in result and result["source_documents"]:
                logging.debug(f"Used {len(result['source_documents'])} knowledge base documents")
        
    except Exception as e:
        logging.error(f"Error analyzing chunk: {str(e)}")
    
    return findings

def scan_single_file(file_path, scan_id, triggered_by, max_chunk_batch=5, cache_enabled=True):
    """Scan a single file for vulnerabilities."""
    file_name = os.path.basename(file_path)
    file_extension = os.path.splitext(file_name)[1][1:].lower()
    logger.info(f"Scanning {file_name}...")

    retrieval_cache = {}  # Simple in-memory cache

    def cache_key(prompt):
        return hashlib.sha256(prompt.encode()).hexdigest()

    def batch_chunks(chunks, batch_size):
        '''Generator Iterator'''    
        for i in range(0, len(chunks), batch_size):
            yield chunks[i:i + batch_size]

    async def async_invoke(prompt):
        qa_chain = get_qa_chain()
        if not qa_chain:
            raise RuntimeError("QA chain not initialized. Call initialize_knowledge_base() first.")
        try:
            result = qa_chain.invoke({"query": prompt})
            return result.get("result", "")
        except Exception as e:
            logger.error(f"Error invoking QA chain: {e}")
            return ""

    async def analyze_chunk_batch(chunk_batch, session):
        findings = []
        for chunk in chunk_batch:
            prompt = create_enhanced_prompt(chunk, file_name, file_extension)
            key = cache_key(prompt)

            if cache_enabled and key in retrieval_cache:
                output = retrieval_cache[key]
                logger.debug(f"Cache hit for chunk in {file_name}")
            else:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory()
                if cpu_percent > 90 or mem.percent > 90:
                    logger.warning(f"High system load, throttling...")
                    await asyncio.sleep(1)

                output = await async_invoke(prompt)
                if cache_enabled:
                    retrieval_cache[key] = output

            findings.extend(extract_relevant_info(llm_output=output, file_name=file_name, file_content=file_content, scan_id=scan_id, triggered_by=triggered_by))

        return findings

    async def process_chunks(chunks):
        all_findings = []
        seen = set()

        async with aiohttp.ClientSession() as session:
            tasks = [analyze_chunk_batch(batch, session) for batch in batch_chunks(chunks, max_chunk_batch)]
            for result in await asyncio.gather(*tasks):
                for finding in result:
                    dedup_key = hashlib.sha256((finding.get("title", "") + finding.get("cwe", "") + finding.get("affected_url", "")).encode()).hexdigest()
                    if dedup_key not in seen:
                        seen.add(dedup_key)
                        all_findings.append(finding)
        return all_findings

    try:
        file_content = read_file(file_path=file_path)

        if len(file_content.strip()) < 50:
            logger.info(f"Skipping {file_name}: file too small.")
            return []

        # Create overlapping chunks
        chunks = []
        start = 0
        while start < len(file_content):
            end = min(start + MAX_TOKENS, len(file_content))
            chunk = file_content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end == len(file_content):
                break
            start = end - 300  # 300-char overlap

        if not chunks:
            chunks = [file_content]

        all_findings = asyncio.run(process_chunks(chunks))
        logger.info(f"Found {len(all_findings)} issues in {file_name}")
        return all_findings

    except Exception as e:
        logger.exception(f"Failed scanning {file_name}")
        return []
