import { useId } from "react";

type BrutalSliderProps = {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  formatValue: (value: number) => string;
  onChange: (value: number) => void;
};

const BrutalSlider = ({
  label,
  value,
  min,
  max,
  step,
  formatValue,
  onChange,
}: BrutalSliderProps) => {
  const id = useId();
  const percent = ((value - min) / (max - min)) * 100;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <label htmlFor={id} className="text-[0.9375rem] font-bold">
          {label}
        </label>
        <span className="rounded-sm border border-hairline bg-accent px-2 py-0.5 font-mono text-sm font-bold text-accent-foreground">
          {formatValue(value)}
        </span>
      </div>

      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="brutal-range h-8 w-full cursor-pointer appearance-none bg-transparent"
        style={{ "--fill": `${percent}%` } as React.CSSProperties}
      />
    </div>
  );
};

export { BrutalSlider };
