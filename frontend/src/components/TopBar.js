import React, { useState } from "react";
import {
  Typography,
  AppBar,
  Toolbar,
  IconButton,
  SwipeableDrawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Slide,
  useScrollTrigger,
  Switch,
} from "@material-ui/core";
import MenuIcon from "@material-ui/icons/Menu";
import LocalLibraryIcon from "@material-ui/icons/LocalLibrary";
import GitHubIcon from "@material-ui/icons/GitHub";
import { useStyles } from "../hooks/useStyles";

function TopBar({ darkMode, setDarkMode }) {
  const classes = useStyles();
  const trigger = useScrollTrigger();

  const [drawerOpen, setDrawerOpen] = useState(false);
  const toggleDrawer = (open) => (event) => {
    // we want to allow Tab/Shift-Tab navigation, so ignore those key presses
    if (
      event &&
      event.type &&
      event.type === "keydown" &&
      (event.key === "Tab" || event.key === "Shift")
    )
      return;

    setDrawerOpen(open);
  };

  const itemsList = () => (
    <div
      className={classes.TopDrawer}
      role="presentation"
      onClick={toggleDrawer(false)}
      onKeyDown={toggleDrawer(false)}
    >
      <List>
        {[
          {
            to: "https://senseis.xmp.net/?BeginnerStudySection",
            text: "How do I play?",
            icon: <LocalLibraryIcon />,
          },
          {
            to: "https://github.com/thisisrandy/igo-frontend",
            text: "Show me the code!",
            icon: <GitHubIcon />,
          },
        ].map(({ to, text, icon }) => (
          <ListItem
            key={to}
            button
            component="a"
            href={to}
            target="_blank"
            rel="noopener noreferrer"
          >
            <ListItemIcon>{icon}</ListItemIcon>
            <ListItemText>{text}</ListItemText>
          </ListItem>
        ))}
      </List>
    </div>
  );

  return (
    <React.Fragment>
      <Slide appear={false} direction="down" in={!trigger}>
        <AppBar position="sticky">
          <Toolbar>
            <IconButton
              edge="start"
              className={classes.TopBarButton}
              color="inherit"
              aria-label="menu"
              aria-controls="main-menu"
              aria-haspopup="true"
              onClick={toggleDrawer(true)}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h5" className={classes.TopBarTitle}>
              囲碁 - igo
            </Typography>
            <Switch
              checked={darkMode}
              onChange={() => setDarkMode((old) => !old)}
            />
          </Toolbar>
        </AppBar>
      </Slide>
      <SwipeableDrawer
        anchor="top"
        open={drawerOpen}
        onOpen={toggleDrawer(true)}
        onClose={toggleDrawer(false)}
      >
        {itemsList()}
      </SwipeableDrawer>
    </React.Fragment>
  );
}

export default TopBar;
