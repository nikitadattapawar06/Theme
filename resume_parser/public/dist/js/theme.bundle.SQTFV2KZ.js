(() => {
  // ../resume_parser/resume_parser/public/js/theme-switcher.js
  frappe.provide("frappe.ui");
  frappe.ui.ThemeSwitcher = class CustomThemeSwitcher extends frappe.ui.ThemeSwitcher {
    constructor() {
      super();
    }
    fetch_themes() {
      return new Promise((resolve) => {
        this.themes = [
          {
            name: "light",
            label: "Frappe Light",
            info: "Light Theme"
          },
          {
            name: "dark",
            label: "Timeless Night",
            info: "Dark Theme"
          },
          {
            name: "automatic",
            label: "Automatic",
            info: "Uses system's theme to switch between light and dark mode"
          },
          {
            name: "intellore-theme",
            label: "Intellore-Theme",
            info: "Our custom theme"
          },
          {
            name: "forest-theme-1",
            label: "Forest-Theme-1",
            info: "New Custom Theme"
          },
          {
            name: "business-theme",
            label: "Business-Theme",
            info: "Professional Theme"
          },
          {
            name: "intellore-theme-1",
            label: "Intellore Theme 1",
            info: "Testing Theme"
          }
        ];
        resolve(this.themes);
      });
    }
    set_theme(theme) {
      super.set_theme(theme);
      document.documentElement.setAttribute("data-theme", theme);
    }
  };

  // ../resume_parser/resume_parser/public/js/theme.bundle.js
  console.log("INJECTED FILE");
})();
//# sourceMappingURL=theme.bundle.SQTFV2KZ.js.map
