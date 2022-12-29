import React from "react";
import Paper from "@material-ui/core/Paper";
import Draggable from "react-draggable";
import { DialogTitle } from "@material-ui/core";
import { ACTIONS_ID, TITLE_ID } from "../constants/Ids";

const titleId = TITLE_ID;
const actionsId = ACTIONS_ID;
const draggableStyle = { cursor: "move" };

/**
 * Using default arguments, this is intended to be used in conjunction with
 * DraggableDialogTitle and DraggableDialogActions in a draggable MUI dialog as
 * described at https://material-ui.com/components/dialogs/#draggable-dialog.
 * You may, however, provide a list of custom element ids as well as a custom
 * cancel selector (see
 * https://github.com/react-grid-layout/react-draggable#draggable-api). Note
 * that props must be supplied via PaperProps on the containing Dialog component
 *
 * Regarding `onStart`, on touch devices, the input field does not blur
 * automatically on drag, which causes some weird behavior (see
 * https://stackoverflow.com/q/67643960/12162258). We can patch that bug by
 * explicitly bluring the input on drag start (see
 * https://stackoverflow.com/a/67745873/12162258 for details). There is also an
 * issue open here: https://github.com/mui-org/material-ui/issues/26494
 */
function DraggablePaper({
  onStart,
  handleIds = [titleId, actionsId],
  cancelSelector = '[class*="MuiDialogContent-root"]',
  ...props
}) {
  // This is to quiet strict mode warnings about findDOMNode usage. See
  // https://stackoverflow.com/a/63603903/12162258 for details
  const nodeRef = React.useRef(null);

  return (
    <Draggable
      handle={handleIds.map((id) => `#${id}`).join(",")}
      cancel={cancelSelector}
      nodeRef={nodeRef}
      onStart={onStart}
    >
      <Paper ref={nodeRef} {...props} />
    </Draggable>
  );
}

function DraggableDialogTitle({ id = titleId, ...props }) {
  return (
    <DialogTitle {...props} style={draggableStyle} id={id}>
      {props.children}
    </DialogTitle>
  );
}

/**
 * IMPORTANT NOTE: using this component with clickable children, e.g. buttons,
 * breaks said children on touch devices. use only with non-interactive children
 */
function DraggableDialogActions({ id = actionsId, ...props }) {
  return (
    <DialogTitle {...props} style={draggableStyle} id={id}>
      {props.children}
    </DialogTitle>
  );
}

export { DraggablePaper, DraggableDialogTitle, DraggableDialogActions };
