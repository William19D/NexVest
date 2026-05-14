/**
 * components/CandlestickChart.tsx
 * -------------------------------
 * Grafico de velas (OHLC) con medias moviles superpuestas, implementado
 * directamente en SVG. No depende de librerias externas de candlestick
 * (Recharts no tiene una primitiva nativa).
 *
 * Cada vela consta de:
 *   - Una linea vertical (mecha) entre 'low' y 'high'.
 *   - Un rectangulo (cuerpo) entre 'open' y 'close'.
 *   - Color verde si close >= open, rojo en caso contrario.
 *
 * Las SMA se dibujan como polilineas sobre el mismo lienzo.
 */

import { useMemo } from "react";

export interface OHLC {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface CandlestickChartProps {
  data: OHLC[];
  sma20?: (number | null)[];
  sma50?: (number | null)[];
  height?: number;
}

const COLOR_ALCISTA = "hsl(166,100%,42%)";
const COLOR_BAJISTA = "hsl(0,72%,51%)";
const COLOR_SMA20 = "hsl(38,92%,50%)";
const COLOR_SMA50 = "hsl(270,60%,60%)";
const COLOR_EJE = "hsl(215,15%,55%)";
const COLOR_GRID = "hsl(220,20%,16%)";

interface PuntoSMA {
  cx: number;
  cy: number;
}

function rangoSMA(valores: (number | null)[] | undefined): PuntoSMA[] | null {
  if (!valores) return null;
  const puntos: PuntoSMA[] = [];
  for (let i = 0; i < valores.length; i++) {
    const v = valores[i];
    if (v !== null && v !== undefined && Number.isFinite(v)) {
      puntos.push({ cx: i, cy: v });
    }
  }
  return puntos;
}

export default function CandlestickChart({
  data,
  sma20,
  sma50,
  height = 360,
}: CandlestickChartProps) {
  const margen = { top: 12, right: 16, bottom: 32, left: 60 };

  const { puntosSMA20, puntosSMA50, dominioY } = useMemo(() => {
    const lows = data.map((d) => d.low);
    const highs = data.map((d) => d.high);
    const valoresSma = [
      ...(sma20 ?? []).filter((v): v is number => v !== null && v !== undefined),
      ...(sma50 ?? []).filter((v): v is number => v !== null && v !== undefined),
    ];
    const min = Math.min(...lows, ...valoresSma);
    const max = Math.max(...highs, ...valoresSma);
    const padding = (max - min) * 0.05;
    return {
      puntosSMA20: rangoSMA(sma20),
      puntosSMA50: rangoSMA(sma50),
      dominioY: [min - padding, max + padding] as [number, number],
    };
  }, [data, sma20, sma50]);

  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-sm text-muted-foreground"
        style={{ height }}
      >
        Sin datos para graficar.
      </div>
    );
  }

  const anchoTotal = 1000;
  const altoTotal = height;
  const anchoUtil = anchoTotal - margen.left - margen.right;
  const altoUtil = altoTotal - margen.top - margen.bottom;
  const pasoX = anchoUtil / Math.max(1, data.length);
  const anchoCuerpo = Math.max(2, Math.min(12, pasoX * 0.65));

  const [yMin, yMax] = dominioY;
  const escalaY = (v: number) =>
    margen.top + altoUtil - ((v - yMin) / (yMax - yMin)) * altoUtil;
  const escalaX = (i: number) =>
    margen.left + pasoX * i + pasoX / 2;

  // Ticks del eje Y: 5 valores equiespaciados.
  const ticksY: number[] = [];
  for (let i = 0; i <= 4; i++) {
    ticksY.push(yMin + ((yMax - yMin) * i) / 4);
  }
  const formatearY = (v: number) =>
    Math.abs(v) >= 1000 ? `${(v / 1000).toFixed(1)}k` : v.toFixed(2);

  // Ticks del eje X: cada ~Math.ceil(n/8) puntos.
  const pasoTickX = Math.max(1, Math.ceil(data.length / 8));
  const ticksX: { i: number; date: string }[] = [];
  for (let i = 0; i < data.length; i += pasoTickX) {
    ticksX.push({ i, date: data[i].date });
  }

  const polilinea = (puntos: PuntoSMA[] | null) => {
    if (!puntos || puntos.length === 0) return "";
    return puntos
      .map((p, i) => `${i === 0 ? "M" : "L"} ${escalaX(p.cx)} ${escalaY(p.cy)}`)
      .join(" ");
  };

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${anchoTotal} ${altoTotal}`} className="w-full" preserveAspectRatio="none">
        {/* Grid horizontal */}
        {ticksY.map((tick) => (
          <line
            key={`grid-${tick}`}
            x1={margen.left}
            x2={anchoTotal - margen.right}
            y1={escalaY(tick)}
            y2={escalaY(tick)}
            stroke={COLOR_GRID}
            strokeDasharray="3 3"
            strokeWidth={1}
          />
        ))}

        {/* Velas */}
        {data.map((d, i) => {
          const cx = escalaX(i);
          const color = d.close >= d.open ? COLOR_ALCISTA : COLOR_BAJISTA;
          const yAlto = escalaY(d.high);
          const yBajo = escalaY(d.low);
          const yApertura = escalaY(d.open);
          const yCierre = escalaY(d.close);
          const yCuerpoTop = Math.min(yApertura, yCierre);
          const altoCuerpo = Math.max(1, Math.abs(yApertura - yCierre));
          return (
            <g key={`vela-${i}`}>
              <line
                x1={cx}
                x2={cx}
                y1={yAlto}
                y2={yBajo}
                stroke={color}
                strokeWidth={1}
              />
              <rect
                x={cx - anchoCuerpo / 2}
                y={yCuerpoTop}
                width={anchoCuerpo}
                height={altoCuerpo}
                fill={color}
                stroke={color}
              />
            </g>
          );
        })}

        {/* SMA20 */}
        {puntosSMA20 && puntosSMA20.length > 0 && (
          <path d={polilinea(puntosSMA20)} stroke={COLOR_SMA20} strokeWidth={1.5} fill="none" />
        )}
        {/* SMA50 */}
        {puntosSMA50 && puntosSMA50.length > 0 && (
          <path d={polilinea(puntosSMA50)} stroke={COLOR_SMA50} strokeWidth={1.5} fill="none" />
        )}

        {/* Eje Y labels */}
        {ticksY.map((tick) => (
          <text
            key={`ty-${tick}`}
            x={margen.left - 6}
            y={escalaY(tick)}
            fontSize={10}
            fill={COLOR_EJE}
            textAnchor="end"
            dominantBaseline="middle"
          >
            {formatearY(tick)}
          </text>
        ))}

        {/* Eje X labels */}
        {ticksX.map(({ i, date }) => (
          <text
            key={`tx-${i}`}
            x={escalaX(i)}
            y={altoTotal - margen.bottom + 14}
            fontSize={9}
            fill={COLOR_EJE}
            textAnchor="middle"
          >
            {date}
          </text>
        ))}
      </svg>

      {/* Leyenda */}
      <div className="mt-2 flex flex-wrap gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-3" style={{ backgroundColor: COLOR_ALCISTA }} /> alcista
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-3" style={{ backgroundColor: COLOR_BAJISTA }} /> bajista
        </span>
        {puntosSMA20 && puntosSMA20.length > 0 && (
          <span className="flex items-center gap-1">
            <span className="inline-block h-0.5 w-4" style={{ backgroundColor: COLOR_SMA20 }} /> SMA20
          </span>
        )}
        {puntosSMA50 && puntosSMA50.length > 0 && (
          <span className="flex items-center gap-1">
            <span className="inline-block h-0.5 w-4" style={{ backgroundColor: COLOR_SMA50 }} /> SMA50
          </span>
        )}
      </div>
    </div>
  );
}
