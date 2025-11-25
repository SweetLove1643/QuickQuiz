import { Search, Plus, Bell, User } from "lucide-react";
import { Button } from "./ui/button";

export function Header() {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white">Q</span>
              </div>
              <span className="text-slate-900">Quizlet</span>
            </div>
            
            {/* Navigation */}
            <nav className="hidden md:flex items-center gap-6">
              <a href="#" className="text-slate-700 hover:text-slate-900 transition-colors">
                Trang chủ
              </a>
              <a href="#" className="text-blue-600 hover:text-blue-700 transition-colors">
                Gần đây
              </a>
              <a href="#" className="text-slate-700 hover:text-slate-900 transition-colors">
                Thư viện
              </a>
            </nav>
          </div>

          {/* Search Bar */}
          <div className="hidden md:flex flex-1 max-w-md mx-8">
            <div className="relative w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-5 text-slate-400" />
              <input
                type="text"
                placeholder="Tìm kiếm bộ thẻ, sách giáo khoa..."
                className="w-full pl-10 pr-4 py-2 bg-slate-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900"
              />
            </div>
          </div>

          {/* Right Side Actions */}
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" className="hidden md:flex">
              <Plus className="size-5" />
            </Button>
            <Button variant="ghost" size="icon" className="hidden md:flex">
              <Bell className="size-5" />
            </Button>
            <Button variant="ghost" size="icon">
              <User className="size-5" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
