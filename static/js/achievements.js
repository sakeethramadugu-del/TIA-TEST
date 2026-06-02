/**
 * Achievement System
 * Handles achievement tracking and display
 */

import { showToast } from "./toast.js";

export async function checkAchievements(action) {
    try {
        const response = await fetch("/api/achievements/check", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ action })
        });
        
        const data = await response.json();
        
        if (data.status === "success" && data.new_achievements.length > 0) {
            // Display achievement popups
            data.new_achievements.forEach((achievement, index) => {
                setTimeout(() => {
                    showAchievementPopup(achievement);
                }, index * 2000); // Stagger popups by 2 seconds
            });
            
            // Show total XP bonus
            if (data.total_xp_bonus > 0) {
                setTimeout(() => {
                    showToast(`Achievement bonus: +${data.total_xp_bonus} XP`, "success");
                }, data.new_achievements.length * 2000 + 500);
            }
        }
    } catch (error) {
        console.error("Failed to check achievements:", error);
    }
}

function showAchievementPopup(achievement) {
    // Create achievement popup element
    const popup = document.createElement("div");
    popup.className = "achievement-popup";
    popup.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
        border: 2px solid #FBBF24;
        border-radius: 16px;
        padding: 24px 32px;
        z-index: 10001;
        text-align: center;
        animation: achievementPop 0.5s ease-out;
        box-shadow: 0 8px 32px rgba(245, 158, 11, 0.4);
        min-width: 320px;
    `;
    
    popup.innerHTML = `
        <div style="font-size: 48px; margin-bottom: 12px;">🏆</div>
        <h3 style="color: white; margin: 0 0 8px 0; font-size: 24px;">Achievement Unlocked!</h3>
        <div style="color: #FEF3C7; font-size: 20px; font-weight: 600; margin-bottom: 8px;">${achievement.name}</div>
        <div style="color: #FEF3C7; font-size: 14px; margin-bottom: 12px;">${achievement.description}</div>
        <div style="color: #FEF3C7; font-size: 16px; font-weight: 600;">+${achievement.xp_bonus} XP</div>
    `;
    
    document.body.appendChild(popup);
    
    // Remove after 4 seconds
    setTimeout(() => {
        popup.style.animation = "achievementFade 0.5s ease-out";
        setTimeout(() => {
            if (popup.parentNode) {
                popup.parentNode.removeChild(popup);
            }
        }, 500);
    }, 4000);
}

// Add CSS animations if not already present
if (!document.getElementById("achievement-animations")) {
    const style = document.createElement("style");
    style.id = "achievement-animations";
    style.textContent = `
        @keyframes achievementPop {
            0% {
                transform: translate(-50%, -50%) scale(0.5);
                opacity: 0;
            }
            50% {
                transform: translate(-50%, -50%) scale(1.1);
            }
            100% {
                transform: translate(-50%, -50%) scale(1);
                opacity: 1;
            }
        }
        @keyframes achievementFade {
            from {
                transform: translate(-50%, -50%) scale(1);
                opacity: 1;
            }
            to {
                transform: translate(-50%, -50%) scale(0.8);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

export async function loadAchievements() {
    try {
        const response = await fetch("/api/achievements");
        const data = await response.json();
        
        if (data.status === "success") {
            return data.achievements;
        }
        return [];
    } catch (error) {
        console.error("Failed to load achievements:", error);
        return [];
    }
}
