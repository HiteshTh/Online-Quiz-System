/* 
   QuizVerse - Pro Developer Anti-Cheat & Safe Exam Security System
   Features:
   - Mandatory Fullscreen Engine with Auto-Prompts & Exit Guard
   - Tab-Switch & Window Blur Detection with Interactive Violation Modals
   - Context Menu (Right-Click) & Clipboard Lock (Copy/Cut/Paste/Select)
   - Inspection & DevTools Keyboard Lockdown (F12, Ctrl+Shift+I/J/C, Ctrl+U/S/P)
   - Real-Time Backend Telemetry Sync & Violation Counter
*/

(function () {
    let tabSwitchCount = 0;
    let isSubmitting = false;
    let isFullscreenMode = false;
    let attemptId = null;

    // Initialize when DOM content is loaded
    document.addEventListener("DOMContentLoaded", function () {
        const pageData = document.getElementById("page-data");
        if (!pageData) return;

        attemptId = pageData.dataset.attemptId;
        if (!attemptId) return;

        initSecurityGuard();
        initFullscreenManager();
        initKeyboardLockdown();
        initClipboardLockdown();
    });

    // ── 1. Fullscreen Engine Manager ──────────────────────────────────────
    function initFullscreenManager() {
        // Create Initial Fullscreen Prompt Modal if browser is not in fullscreen
        if (!document.fullscreenElement && !document.webkitFullscreenElement) {
            showFullscreenPromptModal();
        } else {
            isFullscreenMode = true;
            updateSecurityBadge();
        }

        // Listen for fullscreen change events
        document.addEventListener("fullscreenchange", handleFullscreenChange);
        document.addEventListener("webkitfullscreenchange", handleFullscreenChange);
        document.addEventListener("mozfullscreenchange", handleFullscreenChange);
        document.addEventListener("MSFullscreenChange", handleFullscreenChange);
    }

    function requestFullscreen() {
        const elem = document.documentElement;
        if (elem.requestFullscreen) {
            elem.requestFullscreen().catch(err => console.log("Fullscreen request error:", err));
        } else if (elem.webkitRequestFullscreen) {
            elem.webkitRequestFullscreen();
        } else if (elem.mozRequestFullScreen) {
            elem.mozRequestFullScreen();
        } else if (elem.msRequestFullscreen) {
            elem.msRequestFullscreen();
        }
    }

    function handleFullscreenChange() {
        const isFS = !!(document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement || document.msFullscreenElement);
        isFullscreenMode = isFS;

        updateSecurityBadge();

        if (!isFS && !isSubmitting) {
            // Log security violation for exiting fullscreen
            triggerViolation("Exited Fullscreen Mode during exam");
            showFullscreenExitedModal();
        } else if (isFS) {
            // Remove fullscreen modal if present
            const modal = document.getElementById("fullscreen-security-modal");
            if (modal) modal.remove();
        }
    }

    function showFullscreenPromptModal() {
        if (document.getElementById("fullscreen-security-modal")) return;

        const overlay = document.createElement("div");
        overlay.id = "fullscreen-security-modal";
        overlay.style.cssText = `
            position: fixed; inset: 0; z-index: 99999;
            background: rgba(12, 9, 42, 0.96); backdrop-filter: blur(16px);
            display: flex; align-items: center; justify-content: center; padding: 20px;
        `;

        overlay.innerHTML = `
            <div class="card glass-card text-center p-4 p-md-5 border-teal" style="max-width: 540px; border: 2px solid #05d5ff; box-shadow: 0 0 40px rgba(5, 213, 255, 0.25);">
                <div class="brand-icon-box mx-auto mb-3" style="width: 60px; height: 60px; font-size: 1.8rem; background: linear-gradient(135deg, #05d5ff 0%, #6a5ae0 100%);">
                    <i class="bi bi-arrows-fullscreen"></i>
                </div>
                <h3 class="font-heading fw-bold text-white mb-2">Mandatory Fullscreen Mode</h3>
                <p class="text-secondary small mb-4">
                    QuizVerse Safe Exam Environment requires fullscreen mode to prevent external distractions. Exiting fullscreen during the test will log a security violation.
                </p>
                <button id="btn-enter-fullscreen" class="btn btn-teal-custom py-3 px-4 fw-bold w-100 shadow-lg">
                    <i class="bi bi-shield-lock-fill me-2"></i>Enter Fullscreen &amp; Begin Test
                </button>
            </div>
        `;

        document.body.appendChild(overlay);

        document.getElementById("btn-enter-fullscreen").addEventListener("click", function () {
            requestFullscreen();
            overlay.remove();
        });
    }

    function showFullscreenExitedModal() {
        if (document.getElementById("fullscreen-security-modal")) return;

        const overlay = document.createElement("div");
        overlay.id = "fullscreen-security-modal";
        overlay.style.cssText = `
            position: fixed; inset: 0; z-index: 99999;
            background: rgba(12, 9, 42, 0.96); backdrop-filter: blur(16px);
            display: flex; align-items: center; justify-content: center; padding: 20px;
        `;

        overlay.innerHTML = `
            <div class="card glass-card text-center p-4 p-md-5 border-warning" style="max-width: 540px; border: 2px solid #ff6b6b; box-shadow: 0 0 40px rgba(255, 107, 107, 0.3);">
                <div class="brand-icon-box mx-auto mb-3" style="width: 60px; height: 60px; font-size: 1.8rem; background: linear-gradient(135deg, #ff6b6b 0%, #ff8e53 100%);">
                    <i class="bi bi-exclamation-triangle-fill text-white"></i>
                </div>
                <h3 class="font-heading fw-bold text-white mb-2">SECURITY ALERT: Fullscreen Exited</h3>
                <p class="text-secondary small mb-3">
                    You have exited full screen mode. This action has been logged into your exam attempt security telemetry.
                </p>
                <div class="alert alert-danger py-2 mb-4 font-monospace small">
                    Current Violations: <strong id="modal-violation-count">${tabSwitchCount} / 3</strong>
                </div>
                <button id="btn-reenter-fullscreen" class="btn btn-danger py-3 px-4 fw-bold w-100 shadow-lg">
                    <i class="bi bi-arrows-angle-expand me-2"></i>Re-enter Fullscreen Immediately
                </button>
            </div>
        `;

        document.body.appendChild(overlay);

        document.getElementById("btn-reenter-fullscreen").addEventListener("click", function () {
            requestFullscreen();
            overlay.remove();
        });
    }

    // ── 2. Tab Switch & Blur Guard ───────────────────────────────────────
    function initSecurityGuard() {
        document.addEventListener("visibilitychange", function () {
            if (document.hidden && !isSubmitting) {
                triggerViolation("Tab switch / Minimized window detected");
            }
        });

        window.addEventListener("blur", function () {
            if (!isSubmitting) {
                triggerViolation("Window focus lost");
            }
        });
    }

    function triggerViolation(reason) {
        if (isSubmitting) return;

        tabSwitchCount++;
        updateSecurityBadge();

        // Sync with backend API
        fetch(`/student/attempt/${attemptId}/flag`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ reason: reason })
        })
            .then(res => res.json())
            .then(data => {
                if (data.action === "force_submit" || tabSwitchCount >= 3) {
                    showForceSubmitModal();
                } else {
                    showViolationModal(tabSwitchCount, reason);
                }
            })
            .catch(err => {
                console.error("Anti-cheat telemetry sync error:", err);
                if (tabSwitchCount >= 3) {
                    showForceSubmitModal();
                } else {
                    showViolationModal(tabSwitchCount, reason);
                }
            });
    }

    function showViolationModal(count, reason) {
        // Prevent duplicate popups
        if (document.getElementById("violation-modal")) return;

        const modal = document.createElement("div");
        modal.id = "violation-modal";
        modal.style.cssText = `
            position: fixed; inset: 0; z-index: 99999;
            background: rgba(12, 9, 42, 0.95); backdrop-filter: blur(14px);
            display: flex; align-items: center; justify-content: center; padding: 20px;
        `;

        modal.innerHTML = `
            <div class="card glass-card text-center p-4 p-md-5" style="max-width: 520px; border: 2px solid #ff6b6b; box-shadow: 0 0 50px rgba(255, 107, 107, 0.35);">
                <div class="brand-icon-box mx-auto mb-3" style="width: 64px; height: 64px; font-size: 2rem; background: linear-gradient(135deg, #ef4444 0%, #f97316 100%);">
                    <i class="bi bi-shield-fill-x text-white"></i>
                </div>
                <h3 class="font-heading fw-bold text-white mb-2">SECURITY VIOLATION DETECTED!</h3>
                <p class="text-secondary small mb-3">
                    Leaving the exam screen, switching tabs, or losing window focus is strictly prohibited under QuizVerse Safe Exam Guard.
                </p>

                <div class="p-3 bg-black bg-opacity-40 rounded-3 border border-danger border-opacity-30 mb-4">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="text-secondary small">Reason:</span>
                        <span class="text-warning small font-monospace">${reason}</span>
                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="text-secondary small">Violation Count:</span>
                        <span class="badge bg-danger fs-6">${count} / 3</span>
                    </div>
                </div>

                <p class="text-danger small font-monospace mb-4 fw-semibold">
                    <i class="bi bi-exclamation-octagon me-1"></i> Warning: Reaching 3 violations will automatically submit your exam immediately.
                </p>

                <button id="btn-acknowledge-violation" class="btn btn-danger py-3 px-4 fw-bold w-100 shadow-lg">
                    <i class="bi bi-check-circle-fill me-2"></i>I Understand &amp; Return to Exam
                </button>
            </div>
        `;

        document.body.appendChild(modal);

        document.getElementById("btn-acknowledge-violation").addEventListener("click", function () {
            modal.remove();
            if (!document.fullscreenElement) {
                requestFullscreen();
            }
        });
    }

    function showForceSubmitModal() {
        isSubmitting = true;

        const modal = document.createElement("div");
        modal.id = "force-submit-modal";
        modal.style.cssText = `
            position: fixed; inset: 0; z-index: 999999;
            background: rgba(12, 9, 42, 0.98); backdrop-filter: blur(20px);
            display: flex; align-items: center; justify-content: center; padding: 20px;
        `;

        modal.innerHTML = `
            <div class="card glass-card text-center p-5" style="max-width: 540px; border: 2px solid #ef4444; box-shadow: 0 0 60px rgba(239, 68, 68, 0.5);">
                <div class="spinner-border text-danger mx-auto mb-4" style="width: 3.5rem; height: 3.5rem;" role="status"></div>
                <h3 class="font-heading fw-bold text-white mb-2">EXAM SUBMITTED DUE TO VIOLATIONS</h3>
                <p class="text-secondary small mb-4">
                    Maximum security violation limit (3/3) exceeded. Your exam answers are being finalized and locked immediately.
                </p>
                <div class="progress mb-3" style="height: 6px; background: rgba(255,255,255,0.1);">
                    <div class="progress-bar bg-danger progress-bar-striped progress-bar-animated" style="width: 100%;"></div>
                </div>
                <span class="text-secondary font-monospace small">Submitting telemetry &amp; grading...</span>
            </div>
        `;

        document.body.appendChild(modal);

        setTimeout(() => {
            forceSubmitQuiz();
        }, 1800);
    }

    function forceSubmitQuiz() {
        isSubmitting = true;
        const form = document.getElementById("quiz-form");
        if (form) {
            const flagInput = document.createElement("input");
            flagInput.type = "hidden";
            flagInput.name = "flag_submit";
            flagInput.value = "true";
            form.appendChild(flagInput);
            form.submit();
        }
    }

    // ── 3. Keyboard Lockdown Guard ───────────────────────────────────────
    function initKeyboardLockdown() {
        document.addEventListener("keydown", function (e) {
            // Block F12 (Developer Tools)
            if (e.key === "F12" || e.keyCode === 123) {
                e.preventDefault();
                showSecurityToast("F12 Developer Tools is disabled during exams.");
                return false;
            }

            // Block Ctrl+Shift+I / J / C (DevTools Inspect)
            if (e.ctrlKey && e.shiftKey && (e.key === "I" || e.key === "i" || e.key === "J" || e.key === "j" || e.key === "C" || e.key === "c")) {
                e.preventDefault();
                showSecurityToast("Inspect Element keyboard shortcuts are disabled.");
                return false;
            }

            // Block Cmd+Option+I / J / C (macOS Inspect)
            if (e.metaKey && e.altKey && (e.key === "I" || e.key === "i" || e.key === "J" || e.key === "j" || e.key === "C" || e.key === "c")) {
                e.preventDefault();
                showSecurityToast("Inspect Element keyboard shortcuts are disabled.");
                return false;
            }

            // Block Ctrl+U / Cmd+U (View Source)
            if ((e.ctrlKey || e.metaKey) && (e.key === "u" || e.key === "U")) {
                e.preventDefault();
                showSecurityToast("View Source is disabled during exams.");
                return false;
            }

            // Block Ctrl+S / Ctrl+P (Save / Print)
            if ((e.ctrlKey || e.metaKey) && (e.key === "s" || e.key === "S" || e.key === "p" || e.key === "P")) {
                e.preventDefault();
                showSecurityToast("Save / Print page is disabled during exams.");
                return false;
            }
        });
    }

    // ── 4. Context Menu & Clipboard Guard ──────────────────────────────
    function initClipboardLockdown() {
        // Prevent Right Click Context Menu
        document.addEventListener("contextmenu", function (e) {
            e.preventDefault();
            showSecurityToast("Right-click context menu is disabled.");
            return false;
        });

        // Prevent Copying
        document.addEventListener("copy", function (e) {
            e.preventDefault();
            showSecurityToast("Copying text is disabled during exams.");
            return false;
        });

        // Prevent Cutting
        document.addEventListener("cut", function (e) {
            e.preventDefault();
            showSecurityToast("Cutting text is disabled during exams.");
            return false;
        });

        // Prevent Pasting into inputs unless allowed
        document.addEventListener("paste", function (e) {
            // Allow typing in text inputs, but warn if pasting large external text
            showSecurityToast("External text pasting is monitored.");
        });

        // Prevent Text Selection
        document.addEventListener("selectstart", function (e) {
            // Allow selection inside text input fields
            if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") {
                return true;
            }
            e.preventDefault();
            return false;
        });
    }

    // ── Helper UI Notification Toast ────────────────────────────────────
    function showSecurityToast(msg) {
        let toast = document.getElementById("security-toast-alert");
        if (!toast) {
            toast = document.createElement("div");
            toast.id = "security-toast-alert";
            toast.style.cssText = `
                position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%);
                z-index: 99999; background: rgba(239, 68, 68, 0.95); backdrop-filter: blur(10px);
                color: #ffffff; padding: 10px 20px; border-radius: 50px; font-size: 0.85rem;
                font-family: var(--font-body); font-weight: 600; box-shadow: 0 10px 25px rgba(239, 68, 68, 0.4);
                display: flex; align-items: center; gap: 8px; pointer-events: none; transition: opacity 0.3s ease;
            `;
            document.body.appendChild(toast);
        }

        toast.innerHTML = `<i class="bi bi-shield-lock-fill text-warning"></i> ${msg}`;
        toast.style.opacity = "1";

        clearTimeout(toast._timer);
        toast._timer = setTimeout(() => {
            toast.style.opacity = "0";
        }, 3000);
    }

    function updateSecurityBadge() {
        const countBadge = document.getElementById("security-violation-count");
        if (countBadge) {
            countBadge.innerText = `${tabSwitchCount} / 3`;
            if (tabSwitchCount > 0) {
                countBadge.className = "badge bg-danger text-white ms-1";
            }
        }

        const fsStatus = document.getElementById("fullscreen-status-badge");
        if (fsStatus) {
            if (isFullscreenMode) {
                fsStatus.innerHTML = `<i class="bi bi-arrows-fullscreen text-teal-custom me-1"></i> Fullscreen Locked`;
                fsStatus.className = "badge bg-success bg-opacity-20 text-success border border-success border-opacity-30";
            } else {
                fsStatus.innerHTML = `<i class="bi bi-exclamation-triangle-fill text-warning me-1"></i> Fullscreen Exited`;
                fsStatus.className = "badge bg-warning bg-opacity-20 text-warning border border-warning border-opacity-30";
            }
        }
    }
})();
