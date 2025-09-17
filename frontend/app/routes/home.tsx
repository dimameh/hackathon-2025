import type { Route } from "./+types/home";
import UploadNote from "../UploadDoc";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "CareVoice" },
    { name: "description", content: "Your personal assistant for medical notes" },
  ];
}

export default function Home() {
  return <UploadNote />;
}
