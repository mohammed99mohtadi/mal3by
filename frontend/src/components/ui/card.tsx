import React from "react";
import { Surface, type SurfaceProps } from "@/components/ui/surface";

export const Card = React.forwardRef<HTMLDivElement, SurfaceProps>((props, ref) => <Surface ref={ref} as="article" {...props} />);
Card.displayName = "Card";
