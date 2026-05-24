from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NetworkPolicy:
    external_messages_allowed: bool = False
    external_file_transfers_allowed: bool = False


def default_network_policy() -> NetworkPolicy:
    return NetworkPolicy()


def assert_no_external_transmission(
    *,
    sends_message: bool = False,
    sends_file: bool = False,
    policy: NetworkPolicy | None = None,
) -> None:
    policy = policy or default_network_policy()

    if sends_message and not policy.external_messages_allowed:
        raise PermissionError("External messages are blocked in read-only mode.")

    if sends_file and not policy.external_file_transfers_allowed:
        raise PermissionError("External file transfers are blocked in read-only mode.")
