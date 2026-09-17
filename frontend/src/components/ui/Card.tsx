import type { ReactNode } from "react";

export function Card({
  title,
  subtitle,
  action,
  emphasis = false,
  className = "",
  children,
}: {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  emphasis?: boolean;
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      className={`rounded-xl bg-surface-1 ${
        emphasis ? "border border-border-strong shadow-[0_0_0_1px_rgba(224,145,47,0.06)]" : "border border-border"
      } p-5 ${className}`}
    >
      {(title || action) && (
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            {title && <h3 className="font-mono text-[13px] font-medium text-text-primary">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-[12.5px] text-text-tertiary">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}
