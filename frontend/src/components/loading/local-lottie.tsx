"use client";

import { DotLottieReact, setWasmUrl } from "@lottiefiles/dotlottie-react";

setWasmUrl("/animations/dotlottie-player.wasm");

export default function LocalLottie() {
  return <DotLottieReact src="/animations/invest-analysis.json" autoplay loop />;
}
