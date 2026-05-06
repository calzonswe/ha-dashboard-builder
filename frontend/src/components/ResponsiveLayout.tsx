import React, { useState, useEffect } from 'react'

interface ResponsiveLayoutProps {
  children: React.ReactNode
}

type Breakpoint = 'mobile' | 'tablet' | 'desktop'

const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({ children }) => {
  const [breakpoint, setBreakpoint] = useState<Breakpoint>('desktop')

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth
      if (width < 768) {
        setBreakpoint('mobile')
      } else if (width <= 1024) {
        setBreakpoint('tablet')
      } else {
        setBreakpoint('desktop')
      }
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Pass breakpoint as context via data attribute for child components to use
  const className = `responsive-layout responsive-layout--${breakpoint}`

  return (
    <div className={className} data-breakpoint={breakpoint}>
      {children}
    </div>
  )
}

export default ResponsiveLayout
