import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  Zoom,
} from "@material-ui/core";
import React from "react";
import { useDispatch } from "react-redux";
import { useStyles } from "../hooks/useStyles";
import { DraggablePaper, DraggableDialogTitle } from "./DraggablePaper";

/**
 * A parameterized simple dialog template with a single button which, when
 * clicked, causes the dialog to close
 */
function MessageBase({
  zIndex,
  isOpen,
  title,
  buttonText,
  clickAction,
  children,
}) {
  const classes = useStyles();
  const dispatch = useDispatch();

  const clickHandler = () => dispatch(clickAction());

  return (
    <Dialog
      open={isOpen}
      style={{ zIndex: zIndex }}
      PaperComponent={DraggablePaper}
      // NOTE: for unknown reasons, the outgoing transition is sometimes a
      // combination of whichever transition is chosen and Zoom. Choosing Zoom
      // explicitly patches the weird double-transition bug, so that is what we
      // elect to do. This applies anywhere that a Dialog component is used in
      // this codebase
      TransitionComponent={Zoom}
      onKeyPress={(e) => {
        if (e.key === "Enter") {
          clickHandler();
        }
      }}
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
          onClick={clickHandler}
        >
          {buttonText}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default MessageBase;
