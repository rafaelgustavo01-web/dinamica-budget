#!/usr/bin/env python3
"""
Dinamica Budget — Auto-Training Script for Smart Import / PQ Search

Este script treina modelos para melhorar:
1. Classificação de tipo_recurso (MO, INSUMO, FERRAMENTA, EQUIPAMENTO, SERVICO)
2. Matching de descrições PQ para itens do catálogo
3. Thresholds ótimos por tipo de recurso

Uso:
    python auto_trainer.py --db-url postgresql+asyncpg://... --checkpoint-dir ./checkpoints --log-file training.log

Ou para rodar em background:
    nohup python auto_trainer.py --db-url ... > training.log 2>&1 &
"""

import argparse
import json
import logging
import os
import pickle
import random
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("training.log", mode="a"),
    ],
)
logger = logging.getLogger("auto_trainer")


class TrainingCheckpoint:
    """Gerencia checkpoints de treinamento."""
    
    def __init__(self, checkpoint_dir: str):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.best_score = 0.0
        
    def save(self, model: Any, vectorizer: Any, metadata: dict, iteration: int):
        """Salva checkpoint."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.checkpoint_dir / f"checkpoint_{iteration:04d}_{timestamp}.pkl"
        
        checkpoint = {
            "model": model,
            "vectorizer": vectorizer,
            "metadata": metadata,
            "iteration": iteration,
            "timestamp": timestamp,
        }
        
        with open(filename, "wb") as f:
            pickle.dump(checkpoint, f)
        
        logger.info(f"💾 Checkpoint salvo: {filename}")
        
        # Mantém apenas os 5 checkpoints mais recentes + o melhor
        checkpoints = sorted(self.checkpoint_dir.glob("checkpoint_*.pkl"))
        if len(checkpoints) > 6:
            for old in checkpoints[:-6]:
                old.unlink()
                logger.info(f"🗑️ Checkpoint antigo removido: {old.name}")
    
    def load_latest(self) -> dict | None:
        """Carrega o checkpoint mais recente."""
        checkpoints = sorted(self.checkpoint_dir.glob("checkpoint_*.pkl"))
        if not checkpoints:
            return None
        
        latest = checkpoints[-1]
        with open(latest, "rb") as f:
            checkpoint = pickle.load(f)
        
        logger.info(f"📂 Checkpoint carregado: {latest.name} (iteração {checkpoint['iteration']})")
        return checkpoint


class DataLoader:
    """Carrega e prepara dados de treinamento."""
    
    def __init__(self, db_url: str | None = None):
        self.db_url = db_url
        
    def load_training_data(self) -> tuple[list[str], list[str]]:
        """
        Carrega dados de treinamento.
        Retorna: (descrições, labels_tipo_recurso)
        """
        logger.info("📊 Carregando dados de treinamento...")
        
        # Dados seed para começar (simulados - em produção viriam do banco)
        # Em produção, fazer SELECT de pq_itens + base_tcpo + itens_proprios
        
        seed_data = [
            # SERVIÇOS
            ("Concreto usinado Fck 25 MPa para laje", "SERVICO"),
            ("Mão de obra pedreiro para alvenaria", "SERVICO"),
            ("Revestimento cerâmico parede", "SERVICO"),
            ("Instalação hidráulica completa", "SERVICO"),
            ("Contrapiso de cimento e areia", "SERVICO"),
            ("Forma madeira para concreto", "SERVICO"),
            ("Fundação estaca raiz", "SERVICO"),
            ("Laje pré-moldada concreto", "SERVICO"),
            ("Pintura látex 3 demãos", "SERVICO"),
            ("Sistema elétrico completo", "SERVICO"),
            ("Demolição manual", "SERVICO"),
            ("Limpeza final obra", "SERVICO"),
            ("Escavação manual terra", "SERVICO"),
            ("Aterro compactado", "SERVICO"),
            ("Concreto fck 20 para fundação", "SERVICO"),
            ("Mão de obra servente", "SERVICO"),
            ("Reboco interno", "SERVICO"),
            ("Impermeabilização laje", "SERVICO"),
            ("Esquadria alumínio", "SERVICO"),
            ("Piso cerâmico anti-derrapante", "SERVICO"),
            
            # MÃO DE OBRA
            ("Pedreiro", "MO"),
            ("Servente de pedreiro", "MO"),
            ("Carpinteiro", "MO"),
            ("Encanador", "MO"),
            ("Eletricista", "MO"),
            ("Pintor", "MO"),
            ("Armador de ferro", "MO"),
            ("Mestre de obras", "MO"),
            ("Auxiliar de servente", "MO"),
            
            # EQUIPAMENTOS
            ("Betoneira 400 litros", "EQUIPAMENTO"),
            ("Locação betoneira", "EQUIPAMENTO"),
            ("Compactador manual", "EQUIPAMENTO"),
            ("Andaime tubular", "EQUIPAMENTO"),
            ("Guincho de obra", "EQUIPAMENTO"),
            ("Escavadeira hidráulica", "EQUIPAMENTO"),
            ("Martelete rompedor", "EQUIPAMENTO"),
            ("Serra circular", "EQUIPAMENTO"),
            ("Furadeira industrial", "EQUIPAMENTO"),
            ("Compressor de ar", "EQUIPAMENTO"),
            ("Bomba de concreto", "EQUIPAMENTO"),
            ("Placa vibratória", "EQUIPAMENTO"),
            ("Cortadora de piso", "EQUIPAMENTO"),
            ("Rolo compactador", "EQUIPAMENTO"),
            
            # FERRAMENTAS
            ("Martelo", "FERRAMENTA"),
            ("Nível de mão", "FERRAMENTA"),
            ("Trena 5 metros", "FERRAMENTA"),
            ("Serrote", "FERRAMENTA"),
            ("Alicate universal", "FERRAMENTA"),
            ("Chave de fenda", "FERRAMENTA"),
            ("Chave de roda", "FERRAMENTA"),
            ("Esquadro", "FERRAMENTA"),
            ("Prumo", "FERRAMENTA"),
            ("Desempenadeira", "FERRAMENTA"),
            ("Espátula", "FERRAMENTA"),
            ("Broca concreto 10mm", "FERRAMENTA"),
            ("Serra tico-tico", "FERRAMENTA"),
            ("Lixa manual", "FERRAMENTA"),
            
            # INSUMOS
            ("Cimento Portland CPII-32,5 50kg", "INSUMO"),
            ("Areia média lavada", "INSUMO"),
            ("Brita 1", "INSUMO"),
            ("Aço CA-50 10mm", "INSUMO"),
            ("Aço CA-60 4,2mm", "INSUMO"),
            ("Tijolo cerâmico 8 furos", "INSUMO"),
            ("Bloco de concreto 14x19x39", "INSUMO"),
            ("Tubo PVC 100mm", "INSUMO"),
            ("Fio elétrico 2,5mm", "INSUMO"),
            ("Látex PVA 18 litros", "INSUMO"),
            ("Rejunte cinza", "INSUMO"),
            ("Argamassa colante", "INSUMO"),
            ("Tela soldada 15x15", "INSUMO"),
            ("Vergalhão 12mm", "INSUMO"),
            ("Concreto usinado", "INSUMO"),
            ("Madeira pinus 2x10", "INSUMO"),
            ("Prego 17x27", "INSUMO"),
            ("Parafuso 3/16", "INSUMO"),
            ("Arame recozido", "INSUMO"),
            ("Saco de cal", "INSUMO"),
        ]
        
        descriptions = [item[0] for item in seed_data]
        labels = [item[1] for item in seed_data]
        
        logger.info(f"✅ Dados seed carregados: {len(descriptions)} registros")
        return descriptions, labels
    
    def augment_data(self, descriptions: list[str], labels: list[str]) -> tuple[list[str], list[str]]:
        """Aumenta dados com variações."""
        augmented_desc = []
        augmented_labels = []
        
        for desc, label in zip(descriptions, labels):
            augmented_desc.append(desc)
            augmented_labels.append(label)
            
            # Variações simples
            if label == "EQUIPAMENTO":
                augmented_desc.append(f"Locação de {desc.lower()}")
                augmented_labels.append(label)
                augmented_desc.append(f"Aluguel {desc.lower()}")
                augmented_labels.append(label)
            elif label == "INSUMO":
                augmented_desc.append(f"Material {desc.lower()}")
                augmented_labels.append(label)
                augmented_desc.append(desc.replace("kg", "quilos"))
                augmented_labels.append(label)
            elif label == "MO":
                augmented_desc.append(f"Mão de obra {desc.lower()}")
                augmented_labels.append(label)
            
        logger.info(f"🔀 Dados após augmentação: {len(augmented_desc)} registros")
        return augmented_desc, augmented_labels


class Trainer:
    """Orquestra o treinamento dos modelos."""
    
    def __init__(self, checkpoint_manager: TrainingCheckpoint):
        self.checkpoint_manager = checkpoint_manager
        self.vectorizer = None
        self.classifier = None
        self.is_running = True
        
    def signal_handler(self, signum, frame):
        """Handler para sinais de interrupção."""
        logger.info("🛑 Sinal de interrupção recebido. Finalizando gracefully...")
        self.is_running = False
    
    def train_resource_classifier(self, descriptions: list[str], labels: list[str]) -> dict:
        """
        Treina classificador de tipo_recurso.
        Retorna métricas do treinamento.
        """
        logger.info("🎯 Treinando classificador de tipo_recurso...")
        
        # Vetorização TF-IDF
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            min_df=1,
            max_df=0.95,
            strip_accents="unicode",
            lowercase=True,
        )
        
        X = self.vectorizer.fit_transform(descriptions)
        y = np.array(labels)
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Classificador
        self.classifier = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=2,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced",
        )
        
        self.classifier.fit(X_train, y_train)
        
        # Métricas
        y_pred = self.classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)
        
        logger.info(f"📊 Acurácia: {accuracy:.4f}")
        logger.info(f"📊 F1-score médio: {report['weighted avg']['f1-score']:.4f}")
        
        return {
            "accuracy": accuracy,
            "f1_score": report["weighted avg"]["f1-score"],
            "report": report,
            "classes": list(self.classifier.classes_),
        }
    
    def predict_resource_type(self, description: str) -> tuple[str, float]:
        """Prediz o tipo_recurso de uma descrição."""
        if self.vectorizer is None or self.classifier is None:
            return "SERVICO", 0.0
        
        X = self.vectorizer.transform([description])
        proba = self.classifier.predict_proba(X)[0]
        pred = self.classifier.predict(X)[0]
        confidence = max(proba)
        
        return pred, confidence
    
    def train_threshold_optimizer(self, historical_matches: list[dict]) -> dict:
        """
        Treina otimizador de thresholds baseado em matches históricos.
        
        historical_matches deve ter formato:
        [
            {
                "description": str,
                "tipo_recurso": str,
                "threshold_used": float,
                "match_found": bool,
                "user_confirmed": bool,
            }
        ]
        """
        logger.info("⚙️ Otimizando thresholds...")
        
        # Por tipo_recurso, calcular threshold ótimo
        optimal_thresholds = {
            "SERVICO": 0.65,
            "MO": 0.60,
            "EQUIPAMENTO": 0.50,
            "FERRAMENTA": 0.50,
            "INSUMO": 0.55,
        }
        
        logger.info(f"📐 Thresholds ótimos: {json.dumps(optimal_thresholds, indent=2)}")
        return optimal_thresholds
    
    def run_training_loop(self, iterations: int = 100, sleep_seconds: int = 30):
        """Loop principal de treinamento."""
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        logger.info("🚀 Iniciando loop de treinamento...")
        logger.info(f"   Iterações: {iterations}")
        logger.info(f"   Intervalo: {sleep_seconds}s")
        
        # Carrega dados
        data_loader = DataLoader()
        descriptions, labels = data_loader.load_training_data()
        descriptions, labels = data_loader.augment_data(descriptions, labels)
        
        # Tenta carregar checkpoint anterior
        checkpoint = self.checkpoint_manager.load_latest()
        start_iteration = 0
        if checkpoint:
            self.classifier = checkpoint.get("model")
            self.vectorizer = checkpoint.get("vectorizer")
            start_iteration = checkpoint.get("iteration", 0)
            logger.info(f"🔄 Retomando da iteração {start_iteration}")
        
        # Loop de treinamento
        for iteration in range(start_iteration, iterations):
            if not self.is_running:
                break
            
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 Iteração {iteration + 1}/{iterations}")
            logger.info(f"{'='*60}")
            
            try:
                # 1. Treina classificador
                metrics = self.train_resource_classifier(descriptions, labels)
                
                # 2. Otimiza thresholds (simulado - em produção usaria dados reais)
                thresholds = self.train_threshold_optimizer([])
                
                # 3. Salva checkpoint
                metadata = {
                    "accuracy": metrics["accuracy"],
                    "f1_score": metrics["f1_score"],
                    "thresholds": thresholds,
                    "iteration": iteration + 1,
                    "timestamp": datetime.now().isoformat(),
                }
                
                self.checkpoint_manager.save(
                    model=self.classifier,
                    vectorizer=self.vectorizer,
                    metadata=metadata,
                    iteration=iteration + 1,
                )
                
                # 4. Testa predições
                test_items = [
                    "Betoneira 400 litros",
                    "Concreto fck 25 para laje",
                    "Martelo de carpinteiro",
                    "Cimento 50kg",
                    "Pedreiro diária",
                ]
                
                for item in test_items:
                    pred, conf = self.predict_resource_type(item)
                    logger.info(f"   🧪 {item} → {pred} (conf: {conf:.3f})")
                
                logger.info(f"✅ Iteração {iteration + 1} completa. Acurácia: {metrics['accuracy']:.4f}")
                
            except Exception as e:
                logger.error(f"❌ Erro na iteração {iteration + 1}: {e}")
                logger.exception("Detalhes:")
            
            # Sleep antes da próxima iteração
            if iteration < iterations - 1 and self.is_running:
                logger.info(f"⏳ Aguardando {sleep_seconds}s...")
                time.sleep(sleep_seconds)
        
        logger.info("🏁 Loop de treinamento finalizado.")
        
        # Resumo final
        if self.classifier and self.vectorizer:
            logger.info("\n📈 RESUMO FINAL:")
            logger.info(f"   Iterações completadas: {iteration + 1}")
            logger.info(f"   Classes treinadas: {list(self.classifier.classes_)}")
            logger.info(f"   Última acurácia: {metrics.get('accuracy', 'N/A')}")
            logger.info(f"   Checkpoints em: {self.checkpoint_manager.checkpoint_dir}")


def main():
    parser = argparse.ArgumentParser(description="Dinamica Budget Auto-Trainer")
    parser.add_argument("--db-url", default=None, help="URL do banco de dados PostgreSQL")
    parser.add_argument("--checkpoint-dir", default="./checkpoints", help="Diretório para checkpoints")
    parser.add_argument("--iterations", type=int, default=100, help="Número de iterações")
    parser.add_argument("--sleep", type=int, default=30, help="Segundos entre iterações")
    parser.add_argument("--log-file", default="training.log", help="Arquivo de log")
    
    args = parser.parse_args()
    
    # Atualiza log file se especificado
    if args.log_file:
        file_handler = logging.FileHandler(args.log_file, mode="a")
        file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
        logger.addHandler(file_handler)
    
    logger.info("=" * 70)
    logger.info("🚀 Dinamica Budget Auto-Trainer")
    logger.info("=" * 70)
    logger.info(f"📁 Checkpoints: {args.checkpoint_dir}")
    logger.info(f"🔁 Iterações: {args.iterations}")
    logger.info(f"⏱️  Intervalo: {args.sleep}s")
    logger.info(f"📝 Log: {args.log_file}")
    logger.info("=" * 70)
    
    # Inicializa
    checkpoint_manager = TrainingCheckpoint(args.checkpoint_dir)
    trainer = Trainer(checkpoint_manager)
    
    # Roda treinamento
    trainer.run_training_loop(
        iterations=args.iterations,
        sleep_seconds=args.sleep,
    )


if __name__ == "__main__":
    main()
