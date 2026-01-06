import * as React from 'react';
import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

export interface BarChartDataPoint {
  [key: string]: string | number;
}

export interface BarChartSeries {
  dataKey: string;
  name: string;
  color: string;
  stackId?: string;
}

export interface BarChartProps {
  data: BarChartDataPoint[];
  series: BarChartSeries[];
  xAxisKey: string;
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
  layout?: 'horizontal' | 'vertical';
  yAxisFormatter?: (value: number) => string;
}

export function BarChart({
  data,
  series,
  xAxisKey,
  height = 300,
  showGrid = true,
  showLegend = true,
  layout = 'horizontal',
  yAxisFormatter = (v) => String(v),
}: BarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBarChart
        data={data}
        layout={layout}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />}
        {layout === 'horizontal' ? (
          <>
            <XAxis dataKey={xAxisKey} stroke="#9ca3af" fontSize={12} tickLine={false} />
            <YAxis tickFormatter={yAxisFormatter} stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
          </>
        ) : (
          <>
            <XAxis type="number" tickFormatter={yAxisFormatter} stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis type="category" dataKey={xAxisKey} stroke="#9ca3af" fontSize={12} tickLine={false} width={100} />
          </>
        )}
        <Tooltip
          contentStyle={{
            backgroundColor: '#1f2937',
            border: '1px solid #374151',
            borderRadius: '6px',
            color: '#f3f4f6',
          }}
        />
        {showLegend && <Legend />}
        {series.map((s) => (
          <Bar
            key={s.dataKey}
            dataKey={s.dataKey}
            name={s.name}
            fill={s.color}
            stackId={s.stackId}
            radius={[4, 4, 0, 0]}
          />
        ))}
      </RechartsBarChart>
    </ResponsiveContainer>
  );
}
