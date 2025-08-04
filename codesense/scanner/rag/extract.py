from datetime import datetime
from bson import ObjectId
import logging
import re
import uuid

logger = logging.getLogger(__name__)

def clean_and_validate_field(field_value, max_length=None):
    """Clean and validate field values."""
    if not field_value:
        return ""
    
    # Remove extra whitespace and newlines
    cleaned = ' '.join(field_value.strip().split())
    
    # Apply length limit if specified
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length-3] + "..."
    
    return cleaned

def extract_vulnerable_function(file_content, snippet):
    """Extract the function or class surrounding the vulnerable code."""
    if not snippet or not snippet.strip():
        return "No code snippet available"
    
    try:
        lines = file_content.split('\n')
        snippet_lines = snippet.split('\n')
        
        # Find the line number where the snippet appears
        snippet_line = -1
        for i, line in enumerate(lines):
            if snippet_lines[0].strip() and snippet_lines[0].strip() in line:
                snippet_line = i
                break
        
        if snippet_line == -1:
            return snippet
        
        # Look backwards for function/class definition
        start_line = snippet_line
        function_keywords = [
            'def ', 'function ', 'class ', 'public ', 'private ', 'protected ',
            'static ', 'async ', 'func ', 'proc ', 'sub ', 'method '
        ]
        
        for i in range(snippet_line, max(-1, snippet_line - 50), -1):
            line = lines[i].strip()
            if any(keyword in line for keyword in function_keywords):
                start_line = i
                break
        
        # Look forward for reasonable end point
        end_line = min(snippet_line + 25, len(lines) - 1)
        
        # If we have a substantial context, return it
        extracted = '\n'.join(lines[start_line:end_line + 1])
        return extracted if len(extracted) > len(snippet) else snippet
        
    except Exception as e:
        logging.warning(f"Error extracting function context: {e}")
        return snippet


def extract_relevant_info(llm_output, file_name, scan_id, triggered_by, file_content):
    """Extract relevant security vulnerabilities from the LLM llm_output."""
    if not llm_output or not isinstance(llm_output, str):
        return []

    vulnerabilities = []

    # Enhanced pattern matching for different llm_output formats
    patterns = [
        re.compile(
            r"Vulnerability:\s*(.*?)\s*\n"
            r"CWE:\s*(.*?)\s*\n"
            r"Severity:\s*(.*?)\s*\n"
            r"Impact:\s*(.*?)\s*\n"
            r"Mitigation:\s*(.*?)\s*\n"
            r"Affected:\s*(.*?)\s*\n"
            r"Code Snippet:\s*(.*?)\s*(?=\n\n|\nVulnerability:|\Z)",
            re.DOTALL | re.IGNORECASE
        ),
        re.compile(
            r"(?:Issue|Problem|Security Issue):\s*(.*?)\n"
            r"(?:CWE|Type|Category):\s*(.*?)\n"
            r"(?:Risk|Severity|Level):\s*(.*?)\n"
            r"(?:Description|Impact|Risk Description):\s*(.*?)\n"
            r"(?:Fix|Solution|Mitigation|Recommendation):\s*(.*?)\n"
            r"(?:Location|File|Line|Function):\s*(.*?)\n"
            r"(?:Code|Snippet|Example):\s*(.*?)\s*(?=\n\n|\nIssue:|\Z)",
            re.DOTALL | re.IGNORECASE
        )
    ]

    for pattern in patterns:
        matches = pattern.findall(llm_output)

        for match in matches:
            if len(match) < 7:
                continue

            try:
                title = clean_and_validate_field(match[0], 200)
                cwe = clean_and_validate_field(match[1], 100)
                severity = clean_and_validate_field(match[2], 20).upper()
                impact = clean_and_validate_field(match[3], 1000)
                mitigation = clean_and_validate_field(match[4], 1000)
                affected = clean_and_validate_field(match[5], 200)
                code_snippet = clean_and_validate_field(match[6], 500)

                if not title or not impact:
                    continue

                severity_mapping = {
                    'CRITICAL': ('CRITICAL', '9.8', 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H'),
                    'HIGH':     ('HIGH', '8.8', 'CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H'),
                    'MEDIUM':   ('MEDIUM', '6.5', 'CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:L/A:L'),
                    'LOW':      ('LOW', '3.1', 'CVSS:3.1/AV:L/AC:H/PR:L/UI:R/S:U/C:L/I:N/A:N')
                }

                severity_normalized, cvss_score, cvss_vector = severity_mapping.get(severity, ('MEDIUM', '5.0', 'CVSS:3.1/AV:L/AC:H/PR:L/UI:N/S:U/C:L/I:L/A:N'))

                full_vulnerable_code = extract_vulnerable_function(file_content, code_snippet)

                if cwe and not cwe.upper().startswith('CWE-'):
                    if cwe.isdigit():
                        cwe = f"CWE-{cwe}"
                    elif not any(keyword in cwe.lower() for keyword in ['cwe', 'common weakness']):
                        cwe = f"CWE-{cwe}"

                cwe_number_match = re.search(r'CWE-(\d+)', cwe)
                cwe_number = cwe_number_match.group(1) if cwe_number_match else "NA"
                reference_link = f"https://cwe.mitre.org/data/definitions/{cwe_number}.html" if cwe_number != "NA" else "NA"

                # Auto-generate a PoC description
                pocdesc = f"This proof of concept demonstrates how {title.lower()} can occur. {impact}" if title and impact else "No PoC description provided."

                vulnerability = {
                    "scan_id": ObjectId(scan_id),
                    "cwe": cwe or "CWE-Unknown",
                    "cvss_vector": cvss_vector,
                    "cvss_score": cvss_score,
                    "code": 'f-' + str(uuid.uuid4()).replace('-', '')[:8],
                    "title": title,
                    "description": pocdesc,  # Description = POC description
                    "severity": severity_normalized.lower(),  # Ensure lowercase
                    "file_path": file_name,  # only the file name, not the `affected` part
                    "code_snip": full_vulnerable_code[:2000],  # trimmed snippet
                    "security_risk": impact,
                    "mitigation": mitigation,
                    "status": "open",
                    "deleted": False,
                    "approved": False,
                    "reference": reference_link,
                    "created_at": datetime.utcnow(),
                    "created_by": ObjectId(triggered_by)  # renamed from 'triggered_by'
                }

                vulnerabilities.append(vulnerability)

            except Exception as e:
                logging.warning(f"Error processing vulnerability match: {e}")
                continue

    return vulnerabilities

    