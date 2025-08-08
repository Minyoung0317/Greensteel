declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}

declare module 'react' {
  export = React;
  export as namespace React;
  
  export function useState<T>(initialState: T): [T, (value: T) => void];
  export function useEffect(effect: () => void, deps?: any[]): void;
}

declare module 'next/head' {
  import { ComponentType } from 'react';
  const Head: ComponentType<{
    children?: React.ReactNode;
  }>;
  export default Head;
}

declare module 'axios' {
  const axios: any;
  export default axios;
}

declare namespace React {
  interface ChangeEvent<T = Element> {
    target: T;
  }
  
  interface FormEvent<T = Element> {
    preventDefault(): void;
  }
  
  type ReactNode = any;
}
