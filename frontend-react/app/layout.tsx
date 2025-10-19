import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Link from 'next/link'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Pathio - Smart Career Moves',
  description: 'AI-powered career guidance and job search',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {/* Global Header - Integrated */}
        <div className="bg-black">
          <div className="px-6 py-6">
            <div className="flex items-center">
              <Link href="/?reset=true" className="text-[1.6rem] font-black text-white hover:text-purple-400 transition-colors">
                pathio
              </Link>
            </div>
          </div>
        </div>
        
        {/* Main Content */}
        <div>
          {children}
        </div>
      </body>
    </html>
  )
}

