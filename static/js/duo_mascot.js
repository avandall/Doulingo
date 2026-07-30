/**
 * SVG Duo Owl Mascot Generator & Controller
 * Renders interactive SVG mascot with dynamic emotions.
 */
class DuoMascot {
  static getSVG(state = 'happy') {
    let eyeLeft = `<circle cx="45" cy="55" r="14" fill="#FFF"/><circle cx="45" cy="55" r="7" fill="#3C3C3C"/><circle cx="43" cy="53" r="3" fill="#FFF"/>`;
    let eyeRight = `<circle cx="85" cy="55" r="14" fill="#FFF"/><circle cx="85" cy="55" r="7" fill="#3C3C3C"/><circle cx="43" cy="53" r="3" fill="#FFF"/>`;
    let wingLeft = `<path d="M 15,65 Q 5,80 22,90 Z" fill="#46A302"/>`;
    let wingRight = `<path d="M 115,65 Q 125,80 108,90 Z" fill="#46A302"/>`;
    let mouth = `<path d="M 58,68 Q 65,78 72,68 Z" fill="#FF9600"/>`;
    let extraSparkles = '';

    if (state === 'celebrate') {
      wingLeft = `<path d="M 15,45 Q 5,25 25,35 Z" fill="#46A302"/>`;
      wingRight = `<path d="M 115,45 Q 125,25 105,35 Z" fill="#46A302"/>`;
      mouth = `<path d="M 55,65 Q 65,82 75,65 Z" fill="#FF9600"/>`;
      extraSparkles = `
        <polygon points="20,15 23,22 30,23 24,28 26,35 20,31 14,35 16,28 10,23 17,22" fill="#FFC800"/>
        <polygon points="110,15 113,22 120,23 114,28 116,35 110,31 104,35 106,28 100,23 107,22" fill="#FFC800"/>
      `;
    } else if (state === 'listening') {
      eyeLeft = `<circle cx="45" cy="55" r="14" fill="#FFF"/><circle cx="47" cy="55" r="8" fill="#1CB0F6"/><circle cx="45" cy="53" r="3" fill="#FFF"/>`;
      eyeRight = `<circle cx="85" cy="55" r="14" fill="#FFF"/><circle cx="87" cy="55" r="8" fill="#1CB0F6"/><circle cx="85" cy="53" r="3" fill="#FFF"/>`;
      extraSparkles = `
        <!-- Headphones -->
        <path d="M 25,55 A 40,40 0 0 1 105,55" fill="none" stroke="#FF4B4B" stroke-width="8" stroke-linecap="round"/>
        <rect x="18" y="45" width="14" height="24" rx="7" fill="#FF4B4B"/>
        <rect x="98" y="45" width="14" height="24" rx="7" fill="#FF4B4B"/>
      `;
    } else if (state === 'surprised') {
      eyeLeft = `<circle cx="45" cy="52" r="16" fill="#FFF"/><circle cx="45" cy="52" r="6" fill="#3C3C3C"/>`;
      eyeRight = `<circle cx="85" cy="52" r="16" fill="#FFF"/><circle cx="85" cy="52" r="6" fill="#3C3C3C"/>`;
      mouth = `<circle cx="65" cy="72" r="8" fill="#FF9600"/>`;
    } else if (state === 'thinking') {
      eyeLeft = `<circle cx="45" cy="50" r="14" fill="#FFF"/><circle cx="48" cy="46" r="7" fill="#3C3C3C"/>`;
      eyeRight = `<circle cx="85" cy="50" r="14" fill="#FFF"/><circle cx="88" cy="46" r="7" fill="#3C3C3C"/>`;
      wingLeft = `<path d="M 25,65 Q 45,75 55,68 Z" fill="#46A302"/>`;
    }

    return `
      <svg viewBox="0 0 130 130" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <!-- Duo Body -->
        <ellipse cx="65" cy="70" rx="50" ry="48" fill="#58CC02"/>
        <!-- Belly Patch -->
        <ellipse cx="65" cy="78" rx="36" ry="34" fill="#79E002"/>
        <!-- Feather details on belly -->
        <path d="M 52,70 Q 65,78 78,70" fill="none" stroke="#58CC02" stroke-width="3" stroke-linecap="round"/>
        <path d="M 56,82 Q 65,90 74,82" fill="none" stroke="#58CC02" stroke-width="3" stroke-linecap="round"/>
        
        <!-- Wings -->
        ${wingLeft}
        ${wingRight}

        <!-- Feet -->
        <ellipse cx="48" cy="118" rx="12" ry="6" fill="#FF9600"/>
        <ellipse cx="82" cy="118" rx="12" ry="6" fill="#FF9600"/>

        <!-- Eyes -->
        ${eyeLeft}
        ${eyeRight}

        <!-- Beak/Mouth -->
        ${mouth}

        <!-- Extra overlays (Headphones/Sparkles) -->
        ${extraSparkles}
      </svg>
    `;
  }

  static renderInto(containerId, state = 'happy') {
    const el = document.getElementById(containerId);
    if (el) {
      el.innerHTML = DuoMascot.getSVG(state);
    }
  }
}

window.DuoMascot = DuoMascot;
