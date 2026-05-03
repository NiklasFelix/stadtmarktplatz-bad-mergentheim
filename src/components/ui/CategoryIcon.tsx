import {
  Shirt, BookOpen, UtensilsCrossed, Leaf, Baby, Home,
  Wheat, Gem, Gift, ShoppingBag, type LucideProps
} from 'lucide-react'

const ICON_MAP: Record<string, React.ComponentType<LucideProps>> = {
  Shirt,
  BookOpen,
  UtensilsCrossed,
  Leaf,
  Baby,
  Home,
  Wheat,
  Gem,
  Gift,
  ShoppingBag,
}

interface CategoryIconProps extends LucideProps {
  name: string
}

export function CategoryIcon({ name, ...props }: CategoryIconProps) {
  const Icon = ICON_MAP[name] ?? ShoppingBag
  return <Icon {...props} />
}
