from google import genai
import os
import key as key_module

def format_scan(scan_results):
    summary=scan_results.get("summary",{})
    findings=scan_results.get("findings",[])
    repo_url=scan_results.get("repo_url","Unknown repository")

    formatted=f"""Scan results

    Repository: {repo_url}

    <span class="blue_span">Total files scanned:</span> {summary.get("total_files_scanned",0)}
    <span class="blue_span">Files with secrets:</span> {summary.get("files_with_secrets",0)}
    <span class="blue_span">Files with errors:</span> {summary.get("files_with_errors",0)}

    """

    if len(findings)>0:
        formatted+="SECRETS FOUND:\n"

        for i, finding in enumerate(findings,1):
            filename=finding.get("filename","unknown")
            if "/tmp" in filename:
                filename=filename.split("/")[-1]

            formatted+=f"{i}. File: {filename}\n"

            detectors=finding.get("detectors",{})
            for detector_name, result in detectors.items():
                if not result.get("passed",True):
                    matches_count=result.get("matches_count",0)
                    matches=result.get("matches",[])

                    formatted+=f" {detector_name}:{matches_count} match(es) found\n"

                    if matches and len(matches)>0:
                        first_match=matches[0]

                        if isinstance(first_match, dict):
                            example = first_match.get('string', '')
                        else:
                            example = str(first_match)
                        
                        if len(example) > 50:
                            example = example[:50] + "..."
                        
                        formatted += f"     Example: \"{example}\"\n"

            formatted+="\n"
    else:
        formatted+="RESULT: No secrets detected."

    return formatted
    


def llm_call(prompt_text, api_key):
    try:
        client=genai.Client(api_key=api_key)

        response=client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt_text,
        )

        return response.text
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")
    
def create_prompt(formatted):
    prompt_text=f""" You are working in cybersecurity and your task is to explain potential risks and how to prevent leaks of secrets such as API keys.
            Analyze the following scan results and provide recommended actions:

            {formatted}

            Provide severity assessment, immediate actions and prevention measures. If there is no leaks or warnings, commend the users safety and provide a brief comment on 
            importance of keeping these secrets and keys hidden.
            Try to keep it short and simple.

"""
    
    return prompt_text

def generate_llm(scan_results, api_key):
    try:
        formatted=format_scan(scan_results)

        prompt_text=create_prompt(formatted)
        reccommendations=llm_call(prompt_text, api_key)

        return{
            "success":True,
            "reccommendations":reccommendations,
            "model":"gemini-2.5-flash-lite",
            "formatted_input":formatted
        }
    except Exception as e:
        print(f"LLM generation failed: {str(e)}")
        return {
            "success":False,
            "error":str(e),
            "reccommendations":None
        }

