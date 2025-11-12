/**
 * x402 Insurance - "The Journey" Animated Story Demo
 *
 * An automated, self-playing demo that tells Sarah's story:
 * AI agent developer who discovers x402 Insurance on Solana
 */

let storyDemoRunning = false;
let currentScene = 0;

// Story configuration
const STORY_SCENES = [
    {
        name: "opening",
        duration: 5000,
        overlay: {
            title: "Meet Sarah, an AI Agent Developer",
            subtitle: "Her trading bot makes 10,000 API calls per day",
            style: "intro"
        },
        scroll: { target: "#statsGrid", behavior: "smooth", offset: -100 },
        highlights: ["#totalPolicies", "#totalCoverage"],
        actions: []
    },
    {
        name: "the-problem",
        duration: 8000,
        overlay: {
            title: "What if the API goes down?",
            subtitle: "Lost revenue • Frustrated users • No protection",
            style: "problem"
        },
        scroll: { target: "#recentClaims", behavior: "smooth", offset: -50 },
        callouts: [
            { element: "#recentClaims", text: "503 Service Unavailable", position: "right", style: "error" }
        ],
        actions: [
            { type: "flash-red", target: "#recentClaims", delay: 2000 }
        ]
    },
    {
        name: "the-solution",
        duration: 10000,
        overlay: {
            title: "x402 Insurance: Protection for AI Agents",
            subtitle: "Pay 1% premium • Get instant coverage",
            style: "solution"
        },
        scroll: { target: "#recentPolicies", behavior: "smooth", offset: -50 },
        callouts: [
            { element: "#recentPolicies", text: "Real Solana transactions", position: "right", style: "success" }
        ],
        actions: [
            { type: "pulse", target: "#recentPolicies", delay: 1000 }
        ]
    },
    {
        name: "disaster-strikes",
        duration: 12000,
        overlay: {
            title: "API Outage Detected",
            subtitle: "NovaNet zkEngine generates cryptographic proof",
            style: "alert"
        },
        scroll: { target: "#recentClaims", behavior: "smooth", offset: -50 },
        callouts: [
            { element: "#recentClaims", text: "NovaNet ZK Proof Generated", position: "left", style: "tech", delay: 2000 },
            { element: "#usdcReserve", text: "Instant USDC Refund (400ms)", position: "right", style: "success", delay: 4000 }
        ],
        actions: [
            { type: "start-demo", delay: 0 },
            { type: "highlight", target: "#solanaActivity", delay: 6000 }
        ]
    },
    {
        name: "why-solana",
        duration: 8000,
        overlay: {
            title: "Why Solana?",
            subtitle: "400ms finality • $0.00025 per transaction",
            comparison: {
                left: { title: "Ethereum", finality: "15s", cost: "$5" },
                right: { title: "Solana", finality: "400ms", cost: "$0.00025" }
            },
            style: "comparison"
        },
        scroll: { target: "#blockchainCard", behavior: "smooth", offset: -50 },
        callouts: [
            { element: "#walletAddress", text: "Real-time settlement", position: "bottom", style: "highlight" }
        ],
        actions: []
    },
    {
        name: "tech-stack",
        duration: 10000,
        overlay: {
            title: "The Technology",
            bullets: [
                "NovaNet zkEngine - Cryptographic failure proofs",
                "Solana - Instant settlement (400ms)",
                "USDC - Stable payouts"
            ],
            style: "tech"
        },
        scroll: { target: "#solanaActivity", behavior: "smooth", offset: -50 },
        callouts: [
            { element: "#solanaActivity", text: "Watch real transactions", position: "top", style: "highlight" }
        ],
        actions: [
            { type: "pulse", target: "#solanaActivity", delay: 2000 }
        ]
    },
    {
        name: "live-demo",
        duration: 30000,
        overlay: {
            title: "Live Demo",
            subtitle: "Watch policies and claims in real-time",
            style: "demo"
        },
        scroll: { target: "#recentPolicies", behavior: "smooth", offset: -100 },
        callouts: [],
        actions: [
            { type: "wait-for-demo", delay: 0 }
        ]
    },
    {
        name: "closing",
        duration: 5000,
        overlay: {
            title: "Built on Solana",
            subtitle: "Secured by Zero-Knowledge Proofs",
            style: "closing"
        },
        scroll: { target: "top", behavior: "smooth" },
        actions: []
    }
];

/**
 * Start the story demo
 */
async function startStoryDemo() {
    if (storyDemoRunning) return;

    storyDemoRunning = true;
    currentScene = 0;

    // Hide the start button
    const startBtn = document.getElementById('startDemoBtn');
    if (startBtn) startBtn.style.display = 'none';

    // Create overlay container if it doesn't exist
    createStoryOverlay();

    // Run through all scenes
    for (let i = 0; i < STORY_SCENES.length; i++) {
        if (!storyDemoRunning) break;

        currentScene = i;
        await playScene(STORY_SCENES[i]);
    }

    // End demo
    endStoryDemo();
}

/**
 * Create the overlay container
 */
function createStoryOverlay() {
    let overlay = document.getElementById('storyOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'storyOverlay';
        overlay.innerHTML = `
            <div id="storyContent"></div>
            <div id="storyCallouts"></div>
        `;
        document.body.appendChild(overlay);
    }
    overlay.style.display = 'block';
}

/**
 * Play a single scene
 */
async function playScene(scene) {
    console.log(`Playing scene: ${scene.name}`);

    // Show overlay
    if (scene.overlay) {
        showOverlay(scene.overlay);
    }

    // Scroll to target
    if (scene.scroll) {
        await scrollToElement(scene.scroll);
    }

    // Show callouts
    if (scene.callouts) {
        scene.callouts.forEach(callout => {
            setTimeout(() => {
                showCallout(callout);
            }, callout.delay || 0);
        });
    }

    // Execute actions
    if (scene.actions) {
        scene.actions.forEach(action => {
            setTimeout(() => {
                executeAction(action);
            }, action.delay || 0);
        });
    }

    // Highlight elements
    if (scene.highlights) {
        scene.highlights.forEach(selector => {
            highlightElement(selector);
        });
    }

    // Wait for scene duration
    await new Promise(resolve => setTimeout(resolve, scene.duration));

    // Clear callouts and highlights
    clearCallouts();
    clearHighlights();
}

/**
 * Show full-screen overlay
 */
function showOverlay(overlayConfig) {
    const content = document.getElementById('storyContent');
    let html = '';

    if (overlayConfig.style === 'comparison') {
        html = `
            <div class="story-overlay ${overlayConfig.style}">
                <h1>${overlayConfig.title}</h1>
                <p class="subtitle">${overlayConfig.subtitle}</p>
                <div class="comparison-grid">
                    <div class="comparison-item left">
                        <h3>${overlayConfig.comparison.left.title}</h3>
                        <div class="stat">${overlayConfig.comparison.left.finality}</div>
                        <div class="label">Finality</div>
                        <div class="stat">${overlayConfig.comparison.left.cost}</div>
                        <div class="label">Per Transaction</div>
                    </div>
                    <div class="comparison-vs">VS</div>
                    <div class="comparison-item right">
                        <h3>${overlayConfig.comparison.right.title}</h3>
                        <div class="stat">${overlayConfig.comparison.right.finality}</div>
                        <div class="label">Finality</div>
                        <div class="stat">${overlayConfig.comparison.right.cost}</div>
                        <div class="label">Per Transaction</div>
                    </div>
                </div>
            </div>
        `;
    } else if (overlayConfig.bullets) {
        html = `
            <div class="story-overlay ${overlayConfig.style}">
                <h1>${overlayConfig.title}</h1>
                <ul class="tech-bullets">
                    ${overlayConfig.bullets.map(bullet => `<li>${bullet}</li>`).join('')}
                </ul>
            </div>
        `;
    } else {
        html = `
            <div class="story-overlay ${overlayConfig.style}">
                <h1>${overlayConfig.title}</h1>
                <p class="subtitle">${overlayConfig.subtitle}</p>
            </div>
        `;
    }

    content.innerHTML = html;
    content.style.opacity = '0';
    setTimeout(() => {
        content.style.opacity = '1';
    }, 50);
}

/**
 * Scroll to element smoothly
 */
async function scrollToElement(scrollConfig) {
    const target = scrollConfig.target;

    if (target === 'top') {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
        const element = document.querySelector(target);
        if (element) {
            const offset = scrollConfig.offset || 0;
            const elementPosition = element.getBoundingClientRect().top + window.pageYOffset;
            const offsetPosition = elementPosition + offset;

            window.scrollTo({
                top: offsetPosition,
                behavior: scrollConfig.behavior || 'smooth'
            });
        }
    }

    // Wait for scroll to complete
    await new Promise(resolve => setTimeout(resolve, 1000));
}

/**
 * Show callout annotation
 */
function showCallout(callout) {
    const calloutsContainer = document.getElementById('storyCallouts');
    const storyContent = document.getElementById('storyContent');

    if (!storyContent) return;

    // Get the position of the main overlay box
    const overlayRect = storyContent.getBoundingClientRect();

    const calloutDiv = document.createElement('div');
    calloutDiv.className = `story-callout ${callout.style}`;
    calloutDiv.textContent = callout.text;

    // Position callouts underneath the main overlay box
    // Stack them vertically with some spacing
    const existingCallouts = calloutsContainer.children.length;
    const verticalOffset = existingCallouts * 70; // 70px spacing between callouts

    const left = overlayRect.left + (overlayRect.width / 2); // Center horizontally
    const top = overlayRect.bottom + 40 + verticalOffset; // 40px below overlay, then stack

    calloutDiv.style.transform = 'translateX(-50%)'; // Center the callout

    calloutDiv.style.top = top + 'px';
    calloutDiv.style.left = left + 'px';

    calloutsContainer.appendChild(calloutDiv);

    // Fade in
    setTimeout(() => {
        calloutDiv.style.opacity = '1';
    }, 50);
}

/**
 * Execute action
 */
async function executeAction(action) {
    const element = document.querySelector(action.target);

    switch (action.type) {
        case 'flash-red':
            if (element) {
                element.style.animation = 'flash-red 0.5s ease-in-out 3';
            }
            break;

        case 'pulse':
            if (element) {
                element.style.animation = 'pulse 1s ease-in-out 2';
            }
            break;

        case 'highlight':
            if (element) {
                element.classList.add('highlighted');
            }
            break;

        case 'start-demo':
            // The dashboard shows real data automatically
            // No need to trigger a demo - just let real transactions show
            console.log('Story demo: Showing real dashboard data');
            break;

        case 'wait-for-demo':
            // Wait for the demo to complete
            await new Promise(resolve => setTimeout(resolve, 25000));
            break;
    }
}

/**
 * Highlight element
 */
function highlightElement(selector) {
    const element = document.querySelector(selector);
    if (element) {
        element.classList.add('story-highlighted');
    }
}

/**
 * Clear all callouts
 */
function clearCallouts() {
    const calloutsContainer = document.getElementById('storyCallouts');
    if (calloutsContainer) {
        calloutsContainer.innerHTML = '';
    }
}

/**
 * Clear all highlights
 */
function clearHighlights() {
    document.querySelectorAll('.story-highlighted').forEach(el => {
        el.classList.remove('story-highlighted');
    });
    document.querySelectorAll('.highlighted').forEach(el => {
        el.classList.remove('highlighted');
    });
}

/**
 * End the story demo
 */
function endStoryDemo() {
    storyDemoRunning = false;

    // Hide overlay
    const overlay = document.getElementById('storyOverlay');
    if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => {
            overlay.style.display = 'none';
        }, 500);
    }

    // Clear callouts and highlights
    clearCallouts();
    clearHighlights();

    // Show start button again
    const startBtn = document.getElementById('startDemoBtn');
    if (startBtn) startBtn.style.display = 'block';

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Stop the story demo
 */
function stopStoryDemo() {
    storyDemoRunning = false;
    endStoryDemo();
}
