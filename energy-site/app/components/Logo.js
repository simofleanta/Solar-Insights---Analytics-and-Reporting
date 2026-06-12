export default function Logo({ size = 28 }) {
  return (
    <svg
      width={size}
      height={size * 1.6}
      viewBox="0 0 40 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Light beams — right side of lantern */}
      <line x1="26" y1="9"  x2="40" y2="2"  stroke="white" strokeOpacity="0.55" strokeWidth="1.3" strokeLinecap="round"/>
      <line x1="27" y1="12" x2="40" y2="12" stroke="white" strokeOpacity="0.35" strokeWidth="1.3" strokeLinecap="round"/>
      <line x1="26" y1="15" x2="40" y2="21" stroke="white" strokeOpacity="0.20" strokeWidth="1.3" strokeLinecap="round"/>

      {/* Base */}
      <rect x="2" y="58" width="26" height="5" rx="1" fill="white" fillOpacity="0.85"/>

      {/* Tower — tall, narrow trapezoid */}
      <path d="M9,58 L11,32 L19,32 L21,58 Z" fill="white" fillOpacity="0.80"/>

      {/* Gallery platform — thin horizontal band */}
      <rect x="6" y="29" width="18" height="3" rx="0.5" fill="white" fillOpacity="0.92"/>

      {/* Lantern room — small, vertical rectangle */}
      <rect x="11" y="16" width="8" height="14" rx="1" fill="white" fillOpacity="0.96"/>

      {/* Dome — slim triangle on top */}
      <path d="M12,16 L15,9 L18,16 Z" fill="white" fillOpacity="0.96"/>
    </svg>
  )
}
