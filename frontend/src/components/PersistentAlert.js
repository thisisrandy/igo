import {
  Dialog,
  DialogContent,
  DialogContentText,
  CircularProgress,
  Zoom,
} from "@material-ui/core";
import React from "react";
import { useStyles } from "../hooks/useStyles";
import {
  DraggablePaper,
  DraggableDialogTitle,
  DraggableDialogActions,
} from "./DraggablePaper";

/***
 * This is a display component which should be wrapped with logic to determine a
 * message and openness
 */
function PersistentAlert({ children, zIndex, open }) {
  const classes = useStyles();

  return (
    <React.Fragment>
      <Dialog
        open={open}
        style={{ zIndex: zIndex }}
        PaperComponent={DraggablePaper}
        TransitionComponent={Zoom}
      >
        <DraggableDialogTitle>Alert</DraggableDialogTitle>
        <DialogContent className={classes.DialogContent}>
          <DialogContentText>{children}</DialogContentText>
        </DialogContent>
        <DraggableDialogActions className={classes.AlertProgressContainer}>
          <CircularProgress className={classes.AlertProgress} />
        </DraggableDialogActions>
      </Dialog>
    </React.Fragment>
  );
}

export default PersistentAlert;
