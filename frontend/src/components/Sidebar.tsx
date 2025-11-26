import { Search, Plus, Bell, User, Menu, Home, Clock, Library, X, Upload, FileEdit, Sparkles } from "lucide-react";
import { Button } from "./ui/button";
import { useState } from "react";

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  currentPage: string;
  onNavigate: (page: any) => void;
}

export function Sidebar({ isOpen, onToggle, currentPage, onNavigate }: SidebarProps) {
  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full bg-white border-r border-slate-200 z-50 transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        style={{ width: "280px" }}
      >
        <div className="flex flex-col h-full">
          {/* Header with Logo and Close Button */}
          <div className="flex items-center justify-between p-4 border-b border-slate-200">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white text-xs font-bold">QQ</span>
              </div>
              <span className="text-slate-900 font-normal">QuickQuiz</span>
            </div>
            <Button variant="ghost" size="icon" onClick={onToggle}>
              <X className="size-5" />
            </Button>
          </div>

          {/* Search Bar */}
          <div className="p-4 border-b border-slate-200">
            <div className="relative w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-5 text-slate-400" />
              <input
                type="text"
                placeholder="Tìm kiếm..."
                className="w-full pl-10 pr-4 py-2 bg-slate-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900"
              />
            </div>
          </div>

          {/* Navigation Menu */}
          <nav className="flex-1 p-4 space-y-2">
            <button
              onClick={() => onNavigate("home")}
              className={`flex items-center gap-3 px-4 py-3 w-full rounded-lg transition-colors ${
                currentPage === "home"
                  ? "text-white bg-blue-600"
                  : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              <Home className="size-5" />
              <span>Trang chủ</span>
            </button>
            <button
              onClick={() => onNavigate("quick-start")}
              className={`flex items-center gap-3 px-4 py-3 w-full rounded-lg transition-colors ${
                currentPage === "quick-start"
                  ? "text-white bg-blue-600"
                  : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              <FileEdit className="size-5" />
              <span>Bắt đầu nhanh</span>
            </button>
            <button
              onClick={() => onNavigate("upload-document")}
              className={`flex items-center gap-3 px-4 py-3 w-full rounded-lg transition-colors ${
                currentPage === "upload-document"
                  ? "text-white bg-blue-600"
                  : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              <Upload className="size-5" />
              <span>Upload tài liệu</span>
            </button>
            <button
              onClick={() => onNavigate("create-quiz-standalone")}
              className={`flex items-center gap-3 px-4 py-3 w-full rounded-lg transition-colors ${
                currentPage === "create-quiz-standalone"
                  ? "text-white bg-blue-600"
                  : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              <Sparkles className="size-5" />
              <span>Tạo Quiz</span>
            </button>
            <button
              onClick={() => onNavigate("library")}
              className={`flex items-center gap-3 px-4 py-3 w-full rounded-lg transition-colors ${
                currentPage === "library"
                  ? "text-white bg-blue-600"
                  : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              <Library className="size-5" />
              <span>Thư viện</span>
            </button>
          </nav>

          {/* Bottom Actions */}
          <div className="p-4 border-t border-slate-200 space-y-2">
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon" className="flex-1">
                <Bell className="size-5" />
              </Button>
              <Button variant="ghost" size="icon" className="flex-1">
                <User className="size-5" />
              </Button>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}