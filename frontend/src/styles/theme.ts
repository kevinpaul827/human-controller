import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    primary: {
      main: "#0f6d62",
    },
    secondary: {
      main: "#f4b942",
    },
    background: {
      default: "#f6f7f4",
      paper: "#ffffff",
    },
  },
  shape: {
    borderRadius: 12,
  },
  typography: {
    fontFamily: '"Trebuchet MS", "Segoe UI", sans-serif',
    h3: {
      fontWeight: 700,
    },
    h6: {
      fontWeight: 700,
    },
  },
});

export default theme;
