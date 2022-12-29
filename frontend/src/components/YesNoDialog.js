import {
  Dialog,
  DialogContent,
  DialogContentText,
  Button,
  DialogActions,
  Zoom,
} from "@material-ui/core";
import React from "react";
import { useStyles } from "../hooks/useStyles";
import { DraggableDialogTitle, DraggablePaper } from "./DraggablePaper";

function YesNoDialog({ zIndex, open, title, yesHandler, noHandler, children }) {
  const classes = useStyles();

  return (
    <Dialog
      open={open}
      style={{ zIndex: zIndex }}
      PaperComponent={DraggablePaper}
      TransitionComponent={Zoom}
    >
      <DraggableDialogTitle>{title}</DraggableDialogTitle>
      <DialogContent className={classes.DialogContent}>
        <DialogContentText>{children}</DialogContentText>
      </DialogContent>
      <DialogActions
        disableSpacing={true}
        className={classes.MessageButtonContainer}
      >
        <Button
          className={classes.Button}
          variant="contained"
          onClick={yesHandler}
        >
          Yes
        </Button>
        <Button
          className={classes.Button}
          variant="contained"
          onClick={noHandler}
        >
          No
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default YesNoDialog;
