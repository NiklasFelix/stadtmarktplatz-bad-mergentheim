import { clsx } from 'clsx'
import type { Category } from '../../types'
import { CategoryIcon } from '../ui/CategoryIcon'

interface CategoryFilterProps {
  categories: Category[]
  selectedIds: string[]
  onChange: (ids: string[]) => void
  className?: string
}

export function CategoryFilter({ categories, selectedIds, onChange, className }: CategoryFilterProps) {
  function toggle(id: string) {
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter((s) => s !== id))
    } else {
      onChange([...selectedIds, id])
    }
  }

  return (
    <div className={clsx('flex flex-wrap gap-2', className)}>
      <button
        onClick={() => onChange([])}
        className={clsx(
          'px-4 py-2 rounded-full text-sm font-medium transition-all border',
          selectedIds.length === 0
            ? 'bg-primary-700 text-white border-primary-700'
            : 'bg-white text-gray-600 border-gray-200 hover:border-primary-300 hover:text-primary-700'
        )}
      >
        Alle
      </button>
      {categories.map((cat) => {
        const active = selectedIds.includes(cat.id)
        return (
          <button
            key={cat.id}
            onClick={() => toggle(cat.id)}
            className={clsx(
              'px-4 py-2 rounded-full text-sm font-medium transition-all border',
              active
                ? 'text-white border-transparent'
                : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
            )}
            style={active ? { backgroundColor: cat.color, borderColor: cat.color } : undefined}
          >
            <CategoryIcon
              name={cat.icon}
              size={13}
              className="inline mr-1.5 shrink-0"
              style={active ? { color: 'white' } : { color: cat.color }}
            />
            {cat.name}
          </button>
        )
      })}
    </div>
  )
}
