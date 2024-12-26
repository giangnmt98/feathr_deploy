"""
Module for implementing CRUD operations on various sinks like Redis and MongoDB.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import logging
from rediscluster import RedisCluster
from pymongo.collection import Collection

logger = logging.getLogger(__name__)

class SinkCRUD(ABC):
    """
    Abstract base class for CRUD operations on sinks.
    """

    @abstractmethod
    def _construct_key(self, feature_table: str, input_key: str) -> str:
        """
        Construct a key in the format feature_table:input_key.

        Args:
            feature_table: The name of the feature table.
            input_key: The unique key associated with the data.

        Returns:
            A string key in the format feature_table:input_key.
        """
        pass

    @abstractmethod
    def create(self, feature_table: str, input_key: str, data: Dict[str, Any]) -> None:
        """
        Insert or update data in the sink.

        Args:
            feature_table: The name of the feature table.
            input_key: The unique key associated with the data.
            data: The data to be stored, represented as a dictionary.

        Returns:
            None
        """
        pass

    @abstractmethod
    def read(self, feature_table: str, input_key: str, feature_names: List[str]) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from the sink.

        Args:
            feature_table: The name of the feature table.
            input_key: The unique key associated with the data.
            feature_names: List of feature names to retrieve.

        Returns:
            A dictionary representing the retrieved data, or None if not found.
        """
        pass

    @abstractmethod
    def update(self, feature_table: str, input_key: str, data: Dict[str, Any]) -> None:
        """
        Update existing data in the sink.

        Args:
            feature_table: The name of the feature table.
            input_key: The unique key associated with the data.
            data: The data to update, represented as a dictionary.

        Returns:
            None
        """
        pass

    @abstractmethod
    def delete(self, feature_table: str, input_key: str) -> None:
        """
        Remove data from the sink.

        Args:
            feature_table: The name of the feature table.
            input_key: The unique key associated with the data.

        Returns:
            None
        """
        pass

    @abstractmethod
    def get_all_keys(self, feature_table: str, key_pattern: str) -> List[str]:
        """
        Retrieve all keys matching a pattern from the sink.

        Args:
            feature_table: The name of the feature table.
            key_pattern: The pattern to match keys.

        Returns:
            A list of keys matching the pattern.
        """
        pass

    @abstractmethod
    def truncate(self, feature_table: str) -> None:
        """
        Truncate all data for the specified feature table.

        Args:
            feature_table: The name of the feature table.

        Returns:
            None
        """
        pass

class RedisCRUD(SinkCRUD):
    """
    Implementation of CRUD operations for Redis and Redis Cluster.
    """
    _COMPOSITE_KEY_SEPARATOR = "#"
    _KEY_SEPARATOR = ":"

    def __init__(self, client: Any, is_cluster: bool = False):
        """
        Initialize the RedisCRUD instance.

        Args:
            client: Redis or RedisCluster client instance.
            is_cluster: Boolean flag indicating whether the Redis instance is a cluster.

        Returns:
            None
        """
        self.client = client
        self.is_cluster = is_cluster

    def _construct_key(self, feature_table: str, input_key: str) -> str:
        """
        Construct a Redis key using the feature table name and input key.

        Args:
            feature_table: The name of the feature table.
            input_key: The unique key associated with the data.

        Returns:
            A formatted Redis key string.
        """
        if isinstance(input_key, list):
            input_key = self._COMPOSITE_KEY_SEPARATOR.join(input_key)
        return feature_table + self._KEY_SEPARATOR + input_key

    def create(self, feature_table: str, input_key: str, data: Dict[str, Any]) -> None:
        """
        Insert or update data in Redis.

        Args:
            feature_table: The name of the feature table.
            input_key: The unique key associated with the data.
            data: The data to be stored as a dictionary.

        Returns:
            None
        """
        redis_key = self._construct_key(feature_table, input_key)
        try:
            self.client.hset(redis_key, mapping=data)
            logger.info(f"Data for key '{redis_key}' created/updated successfully.")
        except Exception as e:
            logger.error(f"Error creating/updating data for key '{redis_key}': {e}")

    def read(self, feature_table: str, input_key: str, feature_names: List[str]) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from Redis.

        Args:
            feature_table: The name of the feature table.
            input_key: The unique key associated with the data.
            feature_names: List of feature names to retrieve.

        Returns:
            A dictionary containing the retrieved data, or None if not found.
        """
        redis_key = self._construct_key(feature_table, input_key)
        try:
            data = self.client.hmget(redis_key, *feature_names)
            if not data:
                logger.warning(f"Key '{redis_key}' not found in Redis.")
                return None
            return data
        except Exception as e:
            logger.error(f"Error reading data from Redis for key '{redis_key}': {e}")
            return None

    def update(self, feature_table: str, input_key: str, data: Dict[str, Any]) -> None:
        """
        Update existing data in Redis.

        Args:
            feature_table: The name of the feature table.
            input_key: The unique key associated with the data.
            data: The data to update, represented as a dictionary.

        Returns:
            None
        """
        self.create(feature_table, input_key, data)

    def delete(self, feature_table: str, input_key: str) -> None:
        """
        Remove data from Redis.

        Args:
            feature_table: The name of the feature table.
            input_key: The unique key associated with the data.

        Returns:
            None
        """
        redis_key = self._construct_key(feature_table, input_key)
        try:
            self.client.delete(redis_key)
            logger.info(f"Data for key '{redis_key}' deleted successfully.")
        except Exception as e:
            logger.error(f"Error deleting data for key '{redis_key}': {e}")

    def get_all_keys(self, feature_table: str, key_pattern: str) -> List[str]:
        """
        Retrieve all keys matching a pattern from Redis using _KEY_SEPARATOR and _construct_key.

        Args:
            feature_table: The name of the feature table.
            key_pattern: The pattern to match keys in the feature table.

        Returns:
            A list of input keys (without the feature_table prefix).
        """
        try:
            # Construct the pattern for keys using _KEY_SEPARATOR
            pattern = f"{feature_table}{self._KEY_SEPARATOR}{key_pattern}"
            keys = self.client.keys(pattern)

            # Extract the input keys by removing the feature_table prefix and separator
            return [key.split(f"{feature_table}{self._KEY_SEPARATOR}", 1)[-1] for key in keys]
        except Exception as e:
            logger.error(f"Error retrieving keys for pattern '{key_pattern}': {e}")
            return []

    def truncate(self, feature_table: str) -> None:
        """
        Truncate all data for a feature table in Redis by deleting matching keys.
        """
        try:
            keys_to_delete = self.client.keys(f"{feature_table}:*")
            if keys_to_delete:
                self.client.delete(*keys_to_delete)
            logger.info(f"Truncated all data for feature table '{feature_table}' in Redis.")
        except Exception as e:
            logger.error(f"Error truncating data for feature table '{feature_table}': {e}")

    def multi_read(self, feature_table: str, keys: List[Any], feature_names: List[str]) -> List[List[Any]]:
        """
        Retrieve data for multiple keys from Redis using pipeline.

        Args:
            feature_table: The name of the feature table.
            keys: A list of keys (or composite keys as lists) for which data is to be retrieved.
            feature_names: A list of feature names to retrieve.

        Returns:
            A list of lists containing the values for each key in the order of feature_names.
            If a key is not found, a list of None values is returned for that key.
        """
        try:
            for i in range(len(keys)):
                if isinstance(keys[i], list):
                    keys[i] = self._COMPOSITE_KEY_SEPARATOR.join(keys[i])
            redis_keys = [self._construct_key(feature_table, key) for key in keys]
            with self.client.pipeline() as redis_pipeline:
                for redis_key in redis_keys:
                    redis_pipeline.hmget(redis_key, *feature_names)
                pipeline_result = redis_pipeline.execute()

            results = [
                [value if value is not None else None for value in result] if result else [None] * len(feature_names)
                for result in pipeline_result
            ]
            return results
        except Exception as e:
            logger.error(f"Error reading multiple keys from Redis: {e}")
            return [[None] * len(feature_names) for _ in keys]


class MongoDBCRUD(SinkCRUD):
    """
    Implementation of CRUD operations for MongoDB.
    """
    _COMPOSITE_KEY_SEPARATOR = "#"
    _KEY_SEPARATOR = ":"

    def __init__(self, collection: Collection):
        """
        Initialize the MongoDBCRUD instance.

        Args:
            collection: A pymongo collection instance.

        Returns:
            None
        """
        self.collection = collection

    def _construct_key(self, feature_table: str, input_key: str) -> str:
        """
        Construct a MongoDB key using the feature table name and input key.

        Args:
            feature_table: The name of the feature table.
            input_key: The unique key associated with the data.

        Returns:
            A formatted MongoDB key string.
        """
        if isinstance(input_key, list):
            input_key = self._COMPOSITE_KEY_SEPARATOR.join(input_key)
        return feature_table + self._KEY_SEPARATOR + input_key

    def create(self, feature_table: str, input_key: str, data: Dict[str, Any]) -> None:
        """
        Insert or update data in MongoDB.

        Args:
            feature_table: The name of the feature table.
            input_key: The unique key associated with the data.
            data: The data to be stored as a dictionary.

        Returns:
            None
        """
        key = self._construct_key(feature_table, input_key)
        try:
            self.collection.update_one(
                {"key": key},
                {"$set": {"key": key, "value": data}},
                upsert=True
            )
            logger.info(f"Data for key '{key}' created/updated successfully.")
        except Exception as e:
            logger.error(f"Error creating/updating data for key '{key}': {e}")

    def read(self, feature_table: str, input_key: str, feature_names: List[str]) -> Optional[List[Any]]:
        """
        Retrieve data from MongoDB in the same format as Redis `read`.

        Args:
            feature_table: The name of the feature table.
            input_key: The unique key associated with the data.
            feature_names: List of feature names to retrieve.

        Returns:
            A list of values corresponding to the feature_names, or None if no data is found.
        """
        key = self._construct_key(feature_table, input_key)
        try:
            # Query the document for the specified key
            document = self.collection.find_one({"key": key}, {"value": 1})
            if not document or "value" not in document:
                logger.warning(f"Key '{key}' not found in MongoDB.")
                return None

            # Retrieve the value field
            data = document["value"]

            # Return values in the order of feature_names
            return [data.get(feature, None) for feature in feature_names]
        except Exception as e:
            logger.error(f"Error reading data for key '{key}' in MongoDB: {e}")
            return None

    def update(self, feature_table: str, input_key: str, data: Dict[str, Any]) -> None:
        """
        Update existing data in MongoDB.

        Args:
            feature_table: The name of the feature table.
            input_key: The unique key associated with the data.
            data: The data to update, represented as a dictionary.

        Returns:
            None
        """
        key = self._construct_key(feature_table, input_key)
        try:
            result = self.collection.update_one(
                {"key": key},
                {"$set": {"value": data}}
            )
            if result.matched_count == 0:
                logger.warning(f"Key '{key}' not found for update.")
            else:
                logger.info(f"Data for key '{key}' updated successfully.")
        except Exception as e:
            logger.error(f"Error updating data for key '{key}': {e}")

    def delete(self, feature_table: str, input_key: str) -> None:
        """
        Remove data from MongoDB.

        Args:
            feature_table: The name of the feature table.
            input_key: The unique key associated with the data.

        Returns:
            None
        """
        key = self._construct_key(feature_table, input_key)
        try:
            result = self.collection.delete_one({"key": key})
            if result.deleted_count == 0:
                logger.warning(f"Key '{key}' not found for deletion.")
            else:
                logger.info(f"Data for key '{key}' deleted successfully.")
        except Exception as e:
            logger.error(f"Error deleting data for key '{key}': {e}")

    def get_all_keys(self, feature_table: str, key_pattern: str) -> List[str]:
        """
        Retrieve all keys matching a pattern from MongoDB using _KEY_SEPARATOR and _construct_key.

        Args:
            feature_table: The name of the feature table.
            key_pattern: The pattern to match keys in the feature table.

        Returns:
            A list of input keys (without the feature_table prefix).
        """
        try:
            # Construct the full regex pattern for MongoDB
            full_pattern = f"^{feature_table}{self._KEY_SEPARATOR}{key_pattern}"
            cursor = self.collection.find({"key": {"$regex": full_pattern}}, {"key": 1})

            # Extract the input keys by removing the feature_table prefix and separator
            return [doc["key"].split(f"{feature_table}{self._KEY_SEPARATOR}", 1)[-1] for doc in cursor]
        except Exception as e:
            logger.error(f"Error retrieving keys for pattern '{key_pattern}': {e}")
            return []

    def truncate(self, feature_table: str) -> None:
        """
        Truncate all data for a feature table in MongoDB by deleting all documents.
        """
        try:
            self.collection.delete_many({})
            logger.info(f"Truncated all data for feature table '{feature_table}' in MongoDB.")
        except Exception as e:
            logger.error(f"Error truncating data for feature table '{feature_table}': {e}")

    def multi_read(self, feature_table: str, keys: List[str], feature_names: List[str]) -> List[List[Any]]:
        """
        Retrieve data for multiple keys from MongoDB in a format similar to Redis multi_read.

        Args:
            feature_table: The name of the feature table.
            keys: A list of keys for which data is to be retrieved.
            feature_names: A list of feature names to retrieve.

        Returns:
            A list of lists containing the values for each key in the order of feature_names.
            If a key is not found, a list of None values is returned for that key.
        """
        try:
            for i in range(len(keys)):
                if isinstance(keys[i], list):
                    keys[i] = self._COMPOSITE_KEY_SEPARATOR.join(keys[i])

            formatted_keys = [self._construct_key(feature_table, key) for key in keys]

            cursor = self.collection.find(
                {"key": {"$in": formatted_keys}},
                {"key": 1, "value": 1}
            )

            # Map the key to its values
            data_mapping = {
                doc["key"]: doc.get("value", {})
                for doc in cursor
            }

            results = [
                [data_mapping.get(self._construct_key(feature_table, key), {}).get(feature, None)
                 for feature in feature_names]
                for key in keys
            ]
            return results
        except Exception as e:
            logger.error(f"Error reading multiple keys from MongoDB: {e}")
            return [[None] * len(feature_names) for _ in keys]
