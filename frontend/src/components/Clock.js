import { Paper, Typography } from "@material-ui/core";
import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { TIME_PLAYED, STATUS } from "../constants/StateKeys";
import { useStyles } from "../hooks/useStyles";
import { COMPLETE } from "../constants/GameStatus";
import { GAME } from "../constants/ReducerKeys";

function Clock() {
  const classes = useStyles();
  const { [TIME_PLAYED]: serverTimePlayed, [STATUS]: gameStatus } = useSelector(
    (state) => state[GAME]
  );

  // server time is only updated when a game action is taken to avoid writing to
  // disk and sending updates overly often (see the backend code). instead of
  // ticking on the server end, we can much more efficiently tick on the client
  // side, which we do here
  //
  // NB: when a client first connects, they will start ticking upward from the
  // server time. as such, clients who connect to the same game at different
  // times will display a difference in time played equal to the gap between
  // connection times. this difference will be resolved after any action is
  // taken, because server time will be updated, causing the clients to sync up
  // modulo network latency differences. ultimately, whether the clients' clocks
  // are in perfect sync is not a matter of any real importance, so there's no
  // reason to spend any energy trying to do a better job here
  const [timePlayed, setTimePlayed] = useState(0);
  useEffect(() => {
    if (serverTimePlayed != null) {
      setTimePlayed(serverTimePlayed);
      if (gameStatus !== COMPLETE) {
        const interval = setInterval(
          () => setTimePlayed((prevTimePlayed) => prevTimePlayed + 1),
          1000
        );
        return () => clearInterval(interval);
      }
    } else {
      // NOTE: in the current design, this branch will never be executed,
      // because we never leave a game, i.e. purge its state, without replacing
      // it with a new set of state. Leaving it here in case that changes at
      // some point in the future
      setTimePlayed(0);
    }
  }, [serverTimePlayed, gameStatus]);

  const hhmmss = (seconds) => {
    return (
      (seconds >= 86400 ? Math.floor(seconds / 86400) + "d, " : "") +
      new Date(seconds * 1000).toISOString().slice(11, 19)
    );
  };

  return (
    <Paper className={classes.InfoCardChild}>
      <Typography>Time played: {hhmmss(timePlayed)}</Typography>
    </Paper>
  );
}

export default Clock;
