

export const Alert = ({ children, className = '' }: any) => (
    <div className={`relative w-full rounded-lg border p-4 [&>svg~*]:pl-7 [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground ${className}`} role="alert">{children}</div>
);

export const AlertDescription = ({ children, className = '' }: any) => (
    <div className={`text-sm [&_p]:leading-relaxed ${className}`}>{children}</div>
);
