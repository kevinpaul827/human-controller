type CalibrateSkeletonProps = {
  className?: string;
};

const CalibrateSkeleton = ({ className }: CalibrateSkeletonProps) => (
  <svg
    className={className}
    viewBox="0 0 120 200"
    aria-hidden="true"
    focusable="false"
  >
    <g
      stroke="currentColor"
      strokeWidth={4}
      strokeLinecap="round"
      strokeLinejoin="round"
      fill="currentColor"
    >
      <circle cx={60} cy={24} r={11} stroke="none" />
      <line x1={60} y1={35} x2={60} y2={104} />
      <line x1={60} y1={52} x2={30} y2={92} />
      <line x1={30} y1={92} x2={22} y2={120} />
      <line x1={60} y1={52} x2={92} y2={58} />
      <line x1={92} y1={58} x2={104} y2={34} />
      <line x1={60} y1={104} x2={40} y2={160} />
      <line x1={40} y1={160} x2={36} y2={190} />
      <line x1={60} y1={104} x2={80} y2={160} />
      <line x1={80} y1={160} x2={84} y2={190} />
      <g stroke="none">
        <circle cx={30} cy={92} r={4} />
        <circle cx={22} cy={120} r={4} />
        <circle cx={92} cy={58} r={4} />
        <circle cx={104} cy={34} r={4} />
        <circle cx={60} cy={104} r={4} />
        <circle cx={40} cy={160} r={4} />
        <circle cx={36} cy={190} r={4} />
        <circle cx={80} cy={160} r={4} />
        <circle cx={84} cy={190} r={4} />
      </g>
    </g>
  </svg>
);

export default CalibrateSkeleton;
