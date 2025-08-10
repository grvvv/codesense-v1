def create_enhanced_prompt(chunk, file_name, file_extension):
    """Create an enhanced prompt tailored to the file type."""
    
    # File-specific vulnerability patterns
    vulnerability_focus = {
        'php': [
            'SQL Injection via unsanitized database queries',
            'Cross-Site Scripting (XSS) in output',
            'File inclusion vulnerabilities',
            'Authentication bypass',
            'Session management issues',
            'Command injection',
            'Path traversal'
        ],
        'js': [
            'Cross-Site Scripting (XSS)',
            'Prototype pollution',
            'Code injection via eval()',
            'DOM-based XSS',
            'Insecure API calls',
            'Client-side validation bypass'
        ],
        'py': [
            'SQL Injection',
            'Command injection',
            'Path traversal',
            'Insecure deserialization',
            'Code injection via exec/eval',
            'LDAP injection',
            'Template injection'
        ],
        'java': [
            'SQL Injection',
            'XML External Entity (XXE)',
            'Insecure deserialization',
            'Path traversal',
            'LDAP injection',
            'Expression Language injection'
        ],
        'c': [
            'Buffer overflow',
            'Use after free',
            'Format string vulnerabilities',
            'Integer overflow',
            'Null pointer dereference',
            'Race conditions'
        ],
        'cpp': [
            'Buffer overflow',
            'Use after free',
            'Memory corruption',
            'Integer overflow',
            'Double free',
            'Stack overflow'
        ]
    }
    
    focus_areas = vulnerability_focus.get(file_extension, [
        'Injection vulnerabilities',
        'Authentication issues',
        'Authorization bypass',
        'Input validation problems',
        'Output encoding issues'
    ])
    
    focus_text = '\n'.join([f"- {area}" for area in focus_areas])
    
    return f"""
        You are a security expert analyzing {file_extension.upper()} code for vulnerabilities.

        FOCUS AREAS for {file_extension.upper()}:
        {focus_text}

        IMPORTANT INSTRUCTIONS:
        1. Only report ACTUAL security vulnerabilities, not code quality issues
        2. Be specific about the vulnerability type and impact
        3. Provide concrete mitigation steps
        4. Use the exact format specified below

        For each vulnerability found, use this EXACT format:

        Vulnerability: [Specific vulnerability name]
        CWE: [CWE-XXX format with description]
        Severity: [Critical/Medium/Low/High]
        Impact: [Detailed explanation of security impact and potential exploitation]
        Mitigation: [Specific technical steps to fix the vulnerability]
        Affected: [Function/method name and exact line numbers]
        Code Snippet: [The exact vulnerable code lines]

        ANALYZE THIS CODE:
        ```{file_extension}
        {chunk}
        ```

        File: {file_name}

        Remember: Only report actual security vulnerabilities with clear exploitation potential.
        """
