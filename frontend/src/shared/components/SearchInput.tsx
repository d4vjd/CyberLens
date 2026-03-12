// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

type SearchInputProps = {
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
};

export function SearchInput({ placeholder, value, onChange }: SearchInputProps) {
  return (
    <input
      className="filter-input"
      onChange={(event) => onChange(event.target.value)}
      placeholder={placeholder}
      value={value}
    />
  );
}