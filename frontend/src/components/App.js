import Board from "./Board";
import GameControls from "./GameControls";
import InfoCard from "./InfoCard";
import { useStyles } from "../hooks/useStyles";
import Message from "./Message";
import RequestResponseDialog from "./RequestResponseDialog";
import GameStatusProvider from "./GameStatusProvider";
import RequestResponsePendingAlert from "./RequestResponsePendingAlert";
import ConnectionAlert from "./ConnectionAlert";
import GameRejoiner from "./GameRejoiner";
import ConnectionManager from "./ConnectionManager";
import ErrorMessage from "./ErrorMessage";
import { ALERT_ZINDEX_BASE } from "../constants/AlertZindex";
import EndgameHelpMessage from "./EndgameHelpMessage";
import TopBar from "./TopBar";
import { blueGrey } from "@material-ui/core/colors";
// See https://stackoverflow.com/a/64135466/12162258
import {
  unstable_createMuiStrictModeTheme,
  MuiThemeProvider,
} from "@material-ui/core";
import { CssBaseline } from "@material-ui/core";
import { useStateWithLocalStorage } from "../hooks/useStateWithLocalStorage";
import { DARK_MODE } from "../constants/LocalStorageKeys";
import CentralContainer from "./CentralContainer";

function App() {
  const classes = useStyles();

  const [darkMode, setDarkMode] = useStateWithLocalStorage(DARK_MODE, true);
  const theme = unstable_createMuiStrictModeTheme({
    palette: {
      type: darkMode ? "dark" : "light",
      primary: blueGrey,
    },
  });

  return (
    <MuiThemeProvider theme={theme}>
      <CssBaseline />
      <div className={classes.App}>
        <ConnectionManager />
        <GameRejoiner />
        <RequestResponseDialog zIndex={ALERT_ZINDEX_BASE} />
        <RequestResponsePendingAlert zIndex={ALERT_ZINDEX_BASE} />
        <EndgameHelpMessage zIndex={ALERT_ZINDEX_BASE + 1} />
        <Message zIndex={ALERT_ZINDEX_BASE + 2} />
        <ConnectionAlert zIndex={ALERT_ZINDEX_BASE + 3} />
        <ErrorMessage zIndex={ALERT_ZINDEX_BASE + 4} />
        <TopBar {...{ darkMode, setDarkMode }} />
        <GameStatusProvider>
          <Board />
        </GameStatusProvider>
        <div className={classes.StatusControlsContainer}>
          <GameStatusProvider>
            <GameControls />
            <CentralContainer />
          </GameStatusProvider>
          <InfoCard />
        </div>
      </div>
    </MuiThemeProvider>
  );
}

export default App;
