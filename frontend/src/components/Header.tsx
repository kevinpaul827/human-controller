import { NavLink } from "react-router-dom";
import { Gamepad2, Library, Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import { NAV_ITEMS, ROUTES } from "@/utils/constants";
import ProfileSwitcher from "./ProfileSwitcher";

const navIcons: Record<string, typeof Gamepad2> = {
  [ROUTES.library]: Library,
  [ROUTES.session]: Gamepad2,
  [ROUTES.settings]: Settings,
};

const Header = () => (
  <header className="relative z-10 shrink-0 border-b-2 bg-surface shadow-brutal">
    <div className="mx-auto flex w-full max-w-[1600px] flex-wrap items-center gap-x-6 gap-y-3 px-5 py-3 sm:px-6 lg:px-8">
      <div className="flex items-center gap-2.5">
        <span
          className="flex size-9 items-center justify-center rounded-base border-2 bg-primary text-primary-foreground shadow-brutal-sm"
          aria-hidden="true"
        >
          <Gamepad2 className="size-5" />
        </span>
        <span className="text-base font-bold tracking-tight whitespace-nowrap">
          Human Controller
        </span>
      </div>

      {}
      <nav
        aria-label="Main"
        className="-mx-1 order-last w-full min-w-0 basis-full overflow-x-auto md:order-none md:w-auto md:flex-1 md:basis-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      >
        <ul className="flex items-center gap-1.5 px-1">
          {NAV_ITEMS.map((item) => {
            const Icon = navIcons[item.path];

            return (
              <li key={item.path} className="shrink-0">
                <NavLink
                  to={item.path}
                  end={item.path === "/"}
                  className={({ isActive }) =>
                    cn(
                      "inline-flex h-9 shrink-0 items-center gap-2 rounded-sm border px-3 text-sm font-bold whitespace-nowrap",
                      "transition-[translate,box-shadow] duration-100",
                      isActive
                        ? "bg-accent text-accent-foreground shadow-brutal-sm"
                        : "border-transparent text-foreground hover:translate-x-0.5 hover:translate-y-0.5 hover:border-hairline hover:bg-surface-muted hover:shadow-brutal-sm active:translate-x-1 active:translate-y-1 active:shadow-none",
                    )
                  }
                >
                  {Icon ? <Icon className="size-4" aria-hidden="true" /> : null}
                  {item.label}
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="ml-auto md:ml-0">
        <ProfileSwitcher />
      </div>
    </div>
  </header>
);

export default Header;
