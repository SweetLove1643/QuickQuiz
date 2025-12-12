import { useState, useEffect } from "react";
import { Sidebar } from "../../components/Sidebar";
import { TopBar } from "../../components/TopBar";
import { useAuth } from "../../contexts/AuthContext";

interface AdminUser {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  is_staff: boolean;
  date_joined: string;
}

export const AdminUsers: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const { accessToken } = useAuth();

  // Fetch users from admin API
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await fetch("/admin/api/users/", {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setUsers(data.users || []);
        } else if (response.status === 404) {
          // Fallback: Show message about accessing Django admin
          setError(
            "Admin API not available. Please use Django admin panel at /admin/"
          );
        }
      } catch (err) {
        setError("Failed to load users");
      } finally {
        setIsLoading(false);
      }
    };

    fetchUsers();
  }, [accessToken]);

  const toggleUserStatus = async (userId: string, currentStatus: boolean) => {
    try {
      const response = await fetch(
        `/admin/api/users/${userId}/toggle-status/`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${accessToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ is_active: !currentStatus }),
        }
      );

      if (response.ok) {
        setUsers(
          users.map((u) =>
            u.id === userId ? { ...u, is_active: !currentStatus } : u
          )
        );
      }
    } catch (err) {
      alert("Failed to toggle user status");
    }
  };

  const deleteUser = async (userId: string) => {
    if (!window.confirm("Are you sure you want to delete this user?")) return;

    try {
      const response = await fetch(`/admin/api/users/${userId}/`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (response.ok) {
        setUsers(users.filter((u) => u.id !== userId));
      }
    } catch (err) {
      alert("Failed to delete user");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        currentPage="home"
        onNavigate={() => {}}
      />

      <div
        className={`transition-all duration-300 ${
          isSidebarOpen ? "lg:pl-[280px]" : "pl-0"
        }`}
      >
        <TopBar
          onMenuToggle={() => setIsSidebarOpen(!isSidebarOpen)}
          isSidebarOpen={isSidebarOpen}
          currentPage="home"
          isInQuickStartFlow={false}
        />

        <main className="max-w-7xl mx-auto px-4 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-slate-900 mb-2">
              Quản lý người dùng
            </h1>
            <p className="text-slate-600">Quản lý tài khoản học sinh</p>
          </div>

          {/* Admin Panel Link */}
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-blue-700">
              <strong>Tùy chọn đầy đủ:</strong> Truy cập{" "}
              <a
                href="/admin/"
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium underline hover:no-underline"
              >
                Django Admin Panel
              </a>{" "}
              để quản lý chi tiết người dùng và quyền hạn.
            </p>
          </div>

          {error ? (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-blue-700">
              <p>{error}</p>
              <a
                href="/admin/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-900 font-medium underline hover:no-underline mt-2 inline-block"
              >
                Go to Django Admin →
              </a>
            </div>
          ) : isLoading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                      Username
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                      Joined
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {user.username}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {user.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${
                            user.is_active
                              ? "bg-green-100 text-green-800"
                              : "bg-red-100 text-red-800"
                          }`}
                        >
                          {user.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${
                            user.is_staff
                              ? "bg-purple-100 text-purple-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {user.is_staff ? "Admin" : "Student"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {new Date(user.date_joined).toLocaleDateString("vi-VN")}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                        <button
                          onClick={() =>
                            toggleUserStatus(user.id, user.is_active)
                          }
                          className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                            user.is_active
                              ? "bg-yellow-100 text-yellow-800 hover:bg-yellow-200"
                              : "bg-green-100 text-green-800 hover:bg-green-200"
                          }`}
                        >
                          {user.is_active ? "Deactivate" : "Activate"}
                        </button>
                        {user.username !== "admin" && (
                          <button
                            onClick={() => deleteUser(user.id)}
                            className="px-3 py-1 rounded text-xs font-medium bg-red-100 text-red-800 hover:bg-red-200 transition-colors"
                          >
                            Delete
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!error && !isLoading && users.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-600">No users found</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
