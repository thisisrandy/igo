import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  Zoom,
} from "@material-ui/core";
import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { PLAY, ENDGAME, COMPLETE } from "../constants/GameStatus";
import { STATUS } from "../constants/StateKeys";
import { useStyles } from "../hooks/useStyles";
import { DraggablePaper, DraggableDialogTitle } from "./DraggablePaper";
import { GAME } from "../constants/ReducerKeys";

function EndgameHelpMessage({ zIndex }) {
  const classes = useStyles();
  const { [STATUS]: status } = useSelector((state) => state[GAME]);

  // the goal here is to display this message whenever we transition to the
  // endgame from play. in order to accomplish this, we keep track of when we
  // enter the endgame from any state (mightShow), and whether the user has
  // already been shown this message (shown). shown gets reset if we go back to
  // play and set to true when the user closes the dialog
  const [mightShow, setMightShow] = useState(false);
  const [shown, setShown] = useState(false);
  useEffect(() => {
    // notably, we are not changing any local state when status is
    // REQUEST_PENDING
    if (status === PLAY) {
      setShown(false);
      setMightShow(false);
    } else if (status === ENDGAME) {
      setMightShow(true);
    } else if (status === COMPLETE) {
      setMightShow(false);
    }
  }, [status]);

  return (
    <Dialog
      open={mightShow && !shown}
      style={{ zIndex: zIndex }}
      PaperComponent={DraggablePaper}
      TransitionComponent={Zoom}
    >
      <DraggableDialogTitle>Endgame</DraggableDialogTitle>
      <DialogContent className={classes.DialogContent}>
        <DialogContentText>
          As both players have passed in succession, the endgame has begun.
          Please click on any groups you believe to be dead to mark them as
          such. Your opponent will be given the opportunity to accept or reject
          any marks you make, and likewise you will be given the opportunity to
          respond to any marks your opponent makes. When you are satisfied that
          all dead stones have been removed from the board, click the Request
          Tally Score button, or respond in the affirmative if your opponent
          clicks it first.
        </DialogContentText>
      </DialogContent>
      <DialogActions
        disableSpacing={true}
        className={classes.MessageButtonContainer}
      >
        <Button
          className={classes.Button}
          variant="contained"
          onClick={() => setShown(true)}
        >
          Okay
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default EndgameHelpMessage;
