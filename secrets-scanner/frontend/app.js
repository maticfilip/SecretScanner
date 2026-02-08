//DOM elements
const infoBtn=document.querySelector(".start-btn.info");
const infoBox=document.getElementById("infoBox")

const loadingDiv=document.getElementById("loading");
const resultsDiv=document.getElementById("results");
const findingsDiv=document.getElementById("findings");
const errorDiv=document.getElementById("error");
const summaryDiv=document.getElementById("summary");

const landingView = document.getElementById("landing");
const scannerView = document.getElementById("scanner");
const scanForm=document.getElementById("scanForm");

const getStartedBtn = document.getElementById("getStartedBtn");
const backBtn = document.getElementById("backBtn");

const ORCHESTRATOR_URL="http://localhost:8000";

//UI navigation and UI features
infoBtn.addEventListener("click", ()=>{
    infoBox.style.display=
        infoBox.style.display==="none" || infoBox.style.display===""
            ? "block"
            : "none";
    infoBtn.textContent=
        infoBtn.textContent==="More info" || infoBtn.textContent===""
            ? "Hide info"
            : "More info"
});

function showView(viewToShow) {
    document.querySelectorAll(".view").forEach(view => {
        view.classList.remove("active");
    });

    viewToShow.classList.add("active");
}

getStartedBtn.addEventListener("click", () => {
    showView(scannerView);
});

backBtn.addEventListener("click", () => {
    showView(landingView);
});

function showLoading(){
    loadingDiv.classList.remove("hidden");
}

function hideLoading(){
    loadingDiv.classList.add("hidden");
}

function hideAll(){
    resultsDiv.classList.add("hidden");
    errorDiv.classList.add("hidden");
}

function displayResults(scanResults){
    resultsDiv.classList.remove("hidden");
    displaySummary(scanResults);

    if (scanResults.findings && scanResults.findings.length>0){
        displayFindings(scanResults.findings);
    }else{
        displaySuccessMessage();
    }
}

function displaySummary(scanResults){
    const summary = scanResults.summary;
    const hasSecrets=summary.files_with_secrets>0;

    summaryDiv.innerHTML = `
        <h3>Scan Summary</h3>
        <div class="stat">
            <span>Total Files Scanned:</span>
            <span>${summary.total_files_scanned}</span>
        </div>
        <div class="stat">
            <span>Files with Secrets:</span>
            <span class="stat-value ${hasSecrets ? "danger" : "success"}">
                ${summary.files_with_secrets}
            </span>
        </div>
    `;

    if (scanResults.ai_recommendations){
        if (scanResults.ai_recommendations.success){
            summaryDiv.innerHTML+=`
                <div style="margin-top:20px; padding:15px; border-radius:8px;">
                    <h4>AI Recommendations:</h4>
                    <p style="white-space: pre-wrap;">${scanResults.ai_recommendations.reccommendations}</p>
                </div>
            `;
        } else {
            summaryDiv.innerHTML+=`
                <div style="border: 1px solid #ff9800; padding: 10px; margin-top: 15px; background-color: #fff3e0;">
                    <h4 style="color: #ff9800;">AI Recommendations Unavailable</h4>
                    <p>Error: ${scanResults.ai_recommendations.error || "Failed to generate recommendations"}</p>
                </div>
            `;
        }
    }
}

function displayFindings(findings) {
    findingsDiv.innerHTML = '<h3>Detailed Findings</h3>';
    
    findings.forEach((finding, index) => {
        const div = document.createElement('div');
        div.className = 'finding-item';
        div.innerHTML = `
            <h4> Finding #${index + 1}: ${finding.filename}</h4>
            <p>This file contains potential secrets.</p>
        `;
        findingsDiv.appendChild(div);
    });
}

function displaySuccessMessage(){
    findingsDiv.innerHTML=`
        <div class="success-message">
            <h3> No Secrets Found!</h3>
            <p>The repository appears to be clean.</p>
        </div>
    `;
}

function showError(message){
    errorDiv.classList.remove("hidden");
    errorDiv.innerHTML=`<h3>Error</h3><p>${message}</p>`;
}

//Main functionality

scanForm.addEventListener("submit",async (e) =>{
    e.preventDefault();

    const repoUrl=document.getElementById("repoUrl").value.trim();
    const githubToken=document.getElementById("githubToken").value.trim()

    await scanRepository(repoUrl, githubToken)
})

async function scanRepository(repoUrl, githubToken){
    hideAll();
    showLoading();

    try{
        const scanResults=await performScan(repoUrl, githubToken);
        displayResults(scanResults);
    } catch (error){
        showError(error.message || "An error occurred during scanning.");

    }finally{
        hideLoading();
    }
}

async function performScan(repoUrl, githubToken){
    const requestBody={repo_url:repoUrl};

    if(githubToken){
        requestBody.github_token=githubToken;
    }

    const response=await fetch(`${ORCHESTRATOR_URL}/scan-repo`,{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(requestBody)
    });
        
    if (!response.ok){
        const error=await response.json();
        throw new Error(error.error || `HTTP error! status: ${response.status}`)
    }

    return await response.json();
        

}

