import { Button, Paper } from "@material-ui/core";
import React, { useState } from "react";
import { useStyles } from "../hooks/useStyles";
import { useDispatch, useSelector } from "react-redux";
import { send } from "@giantmachines/redux-websocket";
import { GAME_ACTION } from "../constants/OutgoingMessageTypes";
import { TYPE, KEY, ACTION_TYPE } from "../constants/OutgoingMessageKeys";
import { CONNECTED, KEYS, YOUR_COLOR } from "../constants/StateKeys";
import {
  PASS_TURN,
  REQUEST_DRAW,
  REQUEST_TALLY_SCORE,
  RESIGN,
} from "../constants/GameActionTypes";
import JoinResumeDialog from "./JoinResumeDialog";
import NewGameDialog from "./NewGameDialog";
import YesNoDialog from "./YesNoDialog";
import { ALERT_ZINDEX_BASE } from "../constants/AlertZindex";
import { GAME } from "../constants/ReducerKeys";

function GameControls({ playing, endGame, gameInProgress, myTurn }) {
  const classes = useStyles();
  const {
    [YOUR_COLOR]: yourColor,
    [KEYS]: keys,
    [CONNECTED]: connected,
  } = useSelector((state) => state[GAME]);
  const dispatch = useDispatch();

  const [newGameDialogOpen, setNewGameDialogOpen] = useState(false);
  const newGameButtonClick = () => {
    setNewGameDialogOpen(true);
  };

  const [joinResumeDialogOpen, setJoinResumeDialogOpen] = useState(false);
  const joinResumeGameButtonClick = () => {
    setJoinResumeDialogOpen(true);
  };

  const passButtonClick = () => {
    dispatch(
      send({
        [TYPE]: GAME_ACTION,
        [KEY]: keys[yourColor],
        [ACTION_TYPE]: PASS_TURN,
      })
    );
  };

  const [resignationConfirmationOpen, setResignationConfirmationOpen] =
    useState(false);
  const resignButtonClick = () => {
    setResignationConfirmationOpen(true);
  };
  const resignHandler = (confirmed) => () => {
    setResignationConfirmationOpen(false);
    if (confirmed) {
      dispatch(
        send({
          [TYPE]: GAME_ACTION,
          [KEY]: keys[yourColor],
          [ACTION_TYPE]: RESIGN,
        })
      );
    }
  };

  const requestDrawButtonClick = () => {
    dispatch(
      send({
        [TYPE]: GAME_ACTION,
        [KEY]: keys[yourColor],
        [ACTION_TYPE]: REQUEST_DRAW,
      })
    );
  };

  const requestTallyScore = () => {
    dispatch(
      send({
        [TYPE]: GAME_ACTION,
        [KEY]: keys[yourColor],
        [ACTION_TYPE]: REQUEST_TALLY_SCORE,
      })
    );
  };

  return (
    <Paper className={classes.GameControlsContainer}>
      {gameInProgress ? (
        <React.Fragment>
          <Button
            variant="contained"
            className={classes.Button}
            onClick={passButtonClick}
            disabled={!connected || !playing || !myTurn}
          >
            Pass
          </Button>
          <Button
            variant="contained"
            className={classes.Button}
            onClick={resignButtonClick}
            disabled={!connected || !playing}
          >
            Resign
          </Button>
          <YesNoDialog
            zIndex={ALERT_ZINDEX_BASE}
            open={resignationConfirmationOpen}
            title="Confirmation"
            yesHandler={resignHandler(true)}
            noHandler={resignHandler(false)}
          >
            You elected to resign. Are you certain?
          </YesNoDialog>
          <Button
            variant="contained"
            className={classes.Button}
            onClick={requestDrawButtonClick}
            disabled={!connected || !playing || !myTurn}
          >
            Request Draw
          </Button>
          <Button
            variant="contained"
            className={classes.Button}
            onClick={requestTallyScore}
            disabled={!connected || !endGame}
          >
            Request Tally Score
          </Button>
        </React.Fragment>
      ) : (
        <React.Fragment>
          <Button
            variant="contained"
            className={classes.Button}
            onClick={newGameButtonClick}
            disabled={!connected}
          >
            New Game
          </Button>
          <NewGameDialog {...{ newGameDialogOpen, setNewGameDialogOpen }} />
          <Button
            variant="contained"
            className={classes.Button}
            onClick={joinResumeGameButtonClick}
            disabled={!connected}
          >
            Join/Resume Game
          </Button>
          <JoinResumeDialog
            {...{ joinResumeDialogOpen, setJoinResumeDialogOpen }}
          />
        </React.Fragment>
      )}
    </Paper>
  );
}

export default GameControls;
