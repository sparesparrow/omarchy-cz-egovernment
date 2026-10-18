import QtQuick
import Quickshell
import qs.Commons
import qs.Ui

// All URLs are public, official entry points. Never handle credentials, tokens,
// cookies or Data Box messages in the desktop shell.
BarWidget {
    id: root
    moduleName: "sparesparrow.egovernment"

    readonly property string citizenUrl: "https://obcan.portal.gov.cz/"
    readonly property string identityUrl: "https://www.identita.gov.cz/"
    readonly property string verificationServiceUrl: "https://isform.mf.gov.cz/be/"
    readonly property string dataBoxUrl: "https://datovka.gov.cz/"

    implicitWidth: shortcut.implicitWidth
    implicitHeight: shortcut.implicitHeight

    function openService(button) {
        let url = citizenUrl
        if (button === Qt.MiddleButton)
            url = dataBoxUrl
        else if (button === Qt.RightButton)
            url = verificationServiceUrl
        // Pass argv directly: no shell interpretation or untrusted input.
        Quickshell.execDetached(["xdg-open", url])
    }

    BarIconButton {
        id: shortcut
        anchors.fill: parent
        bar: root.bar
        text: "󰈁"
        slotSize: Style.bar.statusSlot
        tooltipText: "CZ eGovernment: levé – Portál občana, prostřední – Datové schránky, pravé – Elektronicky ověřit identitu (MF / NIA)"
        onPressed: function(button) { root.openService(button) }
    }
}
