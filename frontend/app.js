const wsUrl = "wss://shiny-engine-69pg6j6x6r7x254g6-8000.app.github.dev/ws/telemetry"; // Match your Gateway WS endpoint
const gatewayUrl = "https://shiny-engine-69pg6j6x6r7x254g6-8000.app.github.dev/process"; // Pathway passthrough
const testRunnerUrl = "https://shiny-engine-69pg6j6x6r7x254g6-8001.app.github.dev/run-test";
let socket;
let epsCount = 0;
let totalRequests = 0;

function connectWebSocket() {
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log("Connected to Gateway Telemetry Stream");
        document.querySelector('.orb').style.backgroundColor = 'var(--primary)';
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        // Update Metrics
        if (data.metrics) {
            document.getElementById('eps-val').innerHTML = `${data.metrics.events_per_sec} <span class="unit">EPS</span>`;

            // Wire up the missing Latency DOM element
            if (data.metrics.avg_latency !== undefined) {
                document.getElementById('ttft-val').innerHTML = `${parseFloat(data.metrics.avg_latency).toFixed(1)} <span class="unit">ms</span>`;
            }
        }

        // Handle Events
        if (data.event_type === "anomaly_alert") {
            appendLog('agent-stream', `⚠️ WATCHDOG ALERT: ${data.message || 'Anomaly detected'}`, 'alert');
            let alerts = parseInt(document.getElementById('alerts-val').innerText);
            document.getElementById('alerts-val').innerText = alerts + 1;
        } else if (data.event_type === "tool_call") {
            appendLog('agent-stream', `🔧 Tool Dispatch: ${data.tool_name}(${JSON.stringify(data.arguments)})`, 'tool');
        } else if (data.event_type === "model_thought") {
            appendLog('agent-stream', `🧠 Agent Thought: ${data.thought}`, 'thought');
        } else if (data.event_type === "user_prompt") {
            const msg = (data.payload && data.payload.message) ? data.payload.message : JSON.stringify(data.payload || {});
            appendLog('tickets-stream', `📩 New Ticket [${data.session_id}]: ${msg}`, 'ticket');
        } else if (data.event_type === "TASK_STARTED" || data.event_type === "TASK_COMPLETED" || data.event_type === "TASK_FAILED" || data.event_type === "AGENT_COMPLETED") {
            appendLog('agent-stream', `⚡ ${data.event_type} [${data.session_id || data.task_id}]`, 'thought');
        }
    };

    socket.onclose = () => {
        document.querySelector('.orb').style.backgroundColor = 'var(--alert)';
        setTimeout(connectWebSocket, 3000); // Reconnect
    };
}

function appendLog(elementId, message, typeClass) {
    const window = document.getElementById(elementId);

    // Remove empty state
    const empty = window.querySelector('.empty-state');
    if (empty) empty.remove();

    const entry = document.createElement('div');
    entry.className = `log-entry ${typeClass}`;
    const timestamp = new Date().toISOString().split('T')[1].slice(0, -1);
    entry.innerHTML = `<strong>[${timestamp}]</strong> ${message}`;

    window.appendChild(entry);

    // Auto-scroll
    window.scrollTop = window.scrollHeight;

    // Keep only last 50 logs to prevent DOM lag
    if (window.children.length > 50) {
        window.removeChild(window.firstChild);
    }
}

async function runBackendTest(testName, btnID) {
    const btn = document.getElementById(btnID);
    const allBtns = document.querySelectorAll('.controls .btn');
    const originalText = btn.innerText;

    // Switch active state: deactivate all, activate clicked
    allBtns.forEach(b => {
        b.classList.remove('active', 'primary', 'running');
        b.classList.add('secondary');
    });
    btn.classList.remove('secondary');
    btn.classList.add('active', 'running');
    btn.innerText = "Running...";
    btn.disabled = true;

    try {
        const response = await fetch(`${testRunnerUrl}/${testName}`);
        const data = await response.json();

        appendLog('test-output-stream', `<b>--- Results for ${testName} ---</b>`, 'alert');

        if(data.stdout) {
            data.stdout.split('\n').forEach(line => {
                if(line.trim()) appendLog('test-output-stream', line , 'thought');
            });
        }

        if (data.stderr) {
            data.stderr.split('\n').forEach(line => {
                if(line.trim()) appendLog('test-output-stream', `ERROR: ${line}`, 'alert');
            });
        }

    } catch (err) {
        appendLog('test-output-stream', `Failed to connect to test runner: ${err.message}`, 'alert');
    }
    
    btn.classList.remove('running');
    btn.innerText = originalText;
    btn.disabled = false;
}

// Bind the new buttons
document.getElementById('metrics-test-btn').addEventListener('click', () => runBackendTest('metrics', 'metrics-test-btn'));
document.getElementById('ml-test-btn').addEventListener('click', () => runBackendTest('watchdog', 'ml-test-btn'));
// Override the old stress test button to run the backend Python script instead of the JS loop
document.getElementById('stress-btn').addEventListener('click', () => runBackendTest('stress', 'stress-btn'));

// Init
connectWebSocket();
