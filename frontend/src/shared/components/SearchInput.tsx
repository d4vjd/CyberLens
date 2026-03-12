// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { IconSearch } from "./Icons";

type SearchInputProps = {
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
};

export function SearchInput({ placeholder, value, onChange }: SearchInputProps) {
  return (
    <div className="search-input-wrapper">
      <span className="search-input-wrapper__icon">
        <IconSearch size={15} />
      </span>
      <input
        className="search-input"
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        value={value}
      />
    </div>
  );
}
