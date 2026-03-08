export const toFixedSafe = (value: unknown, digits = 3): string => {
	const num = Number(value);
	if (Number.isNaN(num)) return '-';
	return num.toFixed(digits);
};

export const toPercentSafe = (value: unknown, digits = 1): string => {
	const num = Number(value);
	if (Number.isNaN(num)) return '-';
	return `${(num * 100).toFixed(digits)}%`;
};

export const calcDiff = (a: number, b: number) => {
	const diff = b - a;
	const diffPercent = a === 0 ? null : (diff / a) * 100;
	return { diff, diffPercent };
};

export const pickWinner = (metricName: string, a: number, b: number, modelA: string, modelB: string): string => {
	// Lower is better for latency-like metrics, higher is better for quality metrics.
	const lowerBetter = /耗时|latency|ms/i.test(metricName);
	if (Math.abs(a - b) < 0.0001) return '相近';
	if (lowerBetter) return a < b ? modelA : modelB;
	return a > b ? modelA : modelB;
};
