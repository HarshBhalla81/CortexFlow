const wsUrl = "wss://shiny-engine-69pg6j6x6r7x254g6-8000.app.github.dev/ws/telemetry"; // Match your Gateway WS endpoint
const gatewayUrl = "https://shiny-engine-69pg6j6x6r7x254g6-8000.app.github.dev/process"; // Pathway passthrough

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
            appendLog('agent-stream', `⚠️ WATCHDOG ALERT: ${data.message}`, 'alert');
            let alerts = parseInt(document.getElementById('alerts-val').innerText);
            document.getElementById('alerts-val').innerText = alerts + 1;
        } else if (data.event_type === "tool_call") {
            appendLog('agent-stream', `🔧 Tool Dispatch: ${data.tool_name}(${JSON.stringify(data.arguments)})`, 'tool');
        } else if (data.event_type === "user_prompt") {
            appendLog('tickets-stream', `📩 New Ticket [${data.session_id}]: ${data.payload.message}`, 'ticket');
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
    const timestamp = new Date().toISOString().split('T')[1].slice(0,-1);
    entry.innerHTML = `<strong>[${timestamp}]</strong> ${message}`;
    
    window.appendChild(entry);
    
    // Auto-scroll
    window.scrollTop = window.scrollHeight;

    // Keep only last 50 logs to prevent DOM lag
    if (window.children.length > 50) {
        window.removeChild(window.firstChild);
    }
}

document.getElementById('stress-btn').addEventListener('click', async () => {
    const btn = document.getElementById('stress-btn');
    btn.innerText = "Firing...";
    btn.disabled = true;

    const prompts = [
        "I need a refund for my last order please.",
        "I'm locked out of my account, please reset my password.",
        "How do I track my shipment?",
        "I need to speak to a human manager immediately!",
        "My billing address is incorrect, how do I change it?"
    ];

    // Send a smaller, realistic batch of 20 diverse tickets
    for (let i = 0; i < 20; i++) {
        const sessionId = `ticket-${Math.floor(Math.random() * 10000)}`;
        const randomPrompt = prompts[Math.floor(Math.random() * prompts.length)];
        
        const payload = {
            session_id: sessionId,
            task_id: sessionId,
            event_type: "user_prompt",
            payload: JSON.stringify({ message: randomPrompt }),
            timestamp: Date.now() / 1000.0
        };

        fetch(gatewayUrl, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        }).catch(err => console.error("Request failed", err));
        
        appendLog('tickets-stream', `📩 New Ticket [${sessionId}]: ${randomPrompt.substring(0,25)}...`, 'ticket');
        
        await new Promise(r => setTimeout(r, 200)); // 200ms gap to avoid API rate limits
    }

    btn.innerText = "Launch Stress Test";
    btn.disabled = false;
});

// Init
connectWebSocket();
