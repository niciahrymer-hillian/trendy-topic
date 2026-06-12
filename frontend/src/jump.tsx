// "Jump to" side-panel context.
//
// The user wants every dashboard page to expose a contextual side menu of its key
// entities (all countries, all topics, page sections, ...). Pages publish that list
// here via `useJump`, and the Sidebar renders it. Decoupling this way keeps the
// Sidebar generic and lets each page decide what "jump to" means for its layout.

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

export interface JumpItem {
  label: string;
  onClick: () => void;
  active?: boolean;
}

interface JumpState {
  title: string;
  items: JumpItem[];
  set: (title: string, items: JumpItem[]) => void;
}

const JumpContext = createContext<JumpState | null>(null);

export function JumpProvider({ children }: { children: ReactNode }) {
  const [title, setTitle] = useState("");
  const [items, setItems] = useState<JumpItem[]>([]);
  const set = useCallback((t: string, i: JumpItem[]) => {
    setTitle(t);
    setItems(i);
  }, []);
  const value = useMemo(() => ({ title, items, set }), [title, items, set]);
  return (
    <JumpContext.Provider value={value}>
      {children}
    </JumpContext.Provider>
  );
}

export function useJump(): JumpState {
  const ctx = useContext(JumpContext);
  if (!ctx) throw new Error("useJump must be used inside JumpProvider");
  return ctx;
}

// Convenience for scroll-to-section jump links.
export function scrollToId(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
}
