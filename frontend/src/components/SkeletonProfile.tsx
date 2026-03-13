import { motion } from 'framer-motion';

export default function SkeletonProfile() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-4"
    >
      {/* Header skeleton */}
      <div className="card-glass p-6 space-y-4">
        <div className="flex items-center gap-2">
          <div className="skeleton h-6 w-20 rounded-full" />
          <div className="skeleton h-6 w-28 rounded-full" />
        </div>
        <div className="flex items-start gap-4">
          <div className="skeleton w-16 h-16 rounded-full flex-shrink-0" />
          <div className="flex-1 space-y-3">
            <div className="skeleton h-8 w-56 rounded" />
            <div className="skeleton h-4 w-36 rounded" />
            <div className="flex gap-4">
              <div className="skeleton h-3 w-16 rounded" />
              <div className="skeleton h-3 w-20 rounded" />
              <div className="skeleton h-3 w-24 rounded" />
            </div>
          </div>
        </div>
        <div
          className="flex items-center justify-between pt-3 mt-3"
          style={{ borderTop: '1px solid var(--color-border-subtle)' }}
        >
          <div className="skeleton h-4 w-28 rounded" />
          <div className="skeleton h-6 w-16 rounded" />
        </div>
      </div>

      {/* Grid skeleton: radar + indices */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_0.65fr] gap-4">
        <div className="card-glass p-6">
          <div className="skeleton h-3 w-40 rounded mb-4" />
          <div className="skeleton-radar max-w-[280px] mx-auto" />
        </div>

        <div className="card-glass p-6 space-y-3">
          <div className="skeleton h-3 w-36 rounded mb-4" />
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="space-y-1.5">
              <div className="flex justify-between">
                <div className="skeleton h-3 w-24 rounded" />
                <div className="skeleton h-3 w-10 rounded" />
              </div>
              <div
                className="h-1.5 rounded-full overflow-hidden"
                style={{ background: 'var(--color-surface-2)' }}
              >
                <motion.div
                  className="h-full rounded-full skeleton"
                  style={{ width: `${30 + Math.random() * 50}%` }}
                  initial={{ width: 0 }}
                  animate={{ width: `${30 + Math.random() * 50}%` }}
                  transition={{ duration: 1, delay: i * 0.1 }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
