import React from "react";
import { Dialog } from "@/components/ui/dialog";

export function Drawer(props: React.ComponentProps<typeof Dialog>) { return <Dialog {...props} variant="drawer" />; }
