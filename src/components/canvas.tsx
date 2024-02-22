// from https://medium.com/@pdx.lucasm/canvas-with-react-js-32e133c05258

//import React from 'react';
import { useRef, useEffect } from "react";

export const Canvas = (props: any) => {
  const { draw, options, ...rest } = props;
  //const { context, ...moreConfig } = options;
  const canvasRef = useCanvas(draw);

  return <canvas ref={canvasRef} {...rest} />;
};

export const useCanvas = (draw: (ctx: any, count: number) => void) => {
  const canvasRef: any = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas!.getContext("2d");
    let frameCount = 0;
    let animationFrameId: number;

    const render = () => {
      frameCount++;
      draw(context, frameCount);
      animationFrameId = window.requestAnimationFrame(render);
    };
    render();

    return () => {
      window.cancelAnimationFrame(animationFrameId);
    };
  }, [draw]);

  return canvasRef;
};
