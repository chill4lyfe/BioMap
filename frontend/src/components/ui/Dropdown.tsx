import React from 'react';

interface DropdownProps {
  options: string[];
  selected: string;
  onSelect: (value: string) => void;
  label?: string;
}

export const Dropdown: React.FC<DropdownProps> = ({
  options,
  selected,
  onSelect,
  label,
}) => {
  return (
    <label className="block">
      {label && (
        <span className="mb-2 block text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
          {label}
        </span>
      )}

      <select
        value={selected}
        onChange={(event) => onSelect(event.target.value)}
        className="biomap-select"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
};