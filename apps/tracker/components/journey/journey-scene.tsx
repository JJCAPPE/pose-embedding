"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

export type JourneyStage = "motion" | "encoder" | "space" | "corruption" | "heads" | "results";

export type JourneySceneProps = {
  stage: JourneyStage;
  progress: number;
  recipe: "contrastive" | "contextual" | "supcon";
  corruption: "clean" | "jitter" | "joints" | "frames";
  severity: number;
  playing: boolean;
  frame?: number;
  reducedMotion: boolean;
  view: number;
  onReady: () => void;
  onUnavailable: () => void;
};

const STAGES: JourneyStage[] = ["motion", "encoder", "space", "corruption", "heads", "results"];
const BONES = [[0, 1], [1, 2], [2, 3], [0, 4], [4, 5], [5, 6], [0, 7], [7, 8], [8, 9], [9, 10], [8, 11], [11, 12], [12, 13], [8, 14], [14, 15], [15, 16]];
// Original, mathematical H36M-style figure. No recorded pose or licensed data is used.
const BODY = [[0, -.18, 0], [-.23, -.26, 0], [-.3, -.84, .14], [-.37, -1.43, .1], [.23, -.26, 0], [.34, -.84, -.14], [.46, -1.43, -.1], [0, .18, 0], [0, .62, 0], [0, .83, 0], [0, 1.14, 0], [.36, .62, 0], [.69, .22, .15], [.9, -.08, .32], [-.36, .62, 0], [-.66, .2, -.12], [-.87, -.13, -.3]];
const MASK_ORDER = [13, 12, 11, 16, 15, 14, 3, 6];
const PARTICLES = 1100;
const clamp = THREE.MathUtils.clamp;

function noise(index: number, salt = 1) {
  const value = Math.sin(index * 127.1 + salt * 311.7) * 43758.5453;
  return value - Math.floor(value);
}

function pose(time: number, points = BODY.map(() => new THREE.Vector3())) {
  BODY.forEach(([x, y, z], index) => points[index].set(x, y, z));
  const swing = Math.sin(time);
  const lift = Math.cos(time);
  points[12].set(.63, .45 + lift * .2, .33 + swing * .22);
  points[13].set(.83, .83 + lift * .31, .42 + swing * .45);
  points[15].set(-.62, .25 - lift * .16, -.22 - swing * .25);
  points[16].set(-.78, -.08 - lift * .25, -.26 - swing * .4);
  points[2].z += swing * .35;
  points[3].z += swing * .52;
  points[5].z -= swing * .28;
  points[6].z -= swing * .46;
  points.forEach((point) => { point.y += Math.sin(time * 2) * .035; });
  return points;
}

function material(opacity = 1, metalness = .4) {
  return new THREE.MeshStandardMaterial({ color: 0xe8e8e8, roughness: .28, metalness, transparent: true, opacity });
}

function lineMaterial(opacity = .2) {
  return new THREE.LineBasicMaterial({ color: 0xe9e9e9, transparent: true, opacity, depthWrite: false });
}

function line(points: THREE.Vector3[], opacity = .2, loop = false) {
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  return loop ? new THREE.LineLoop(geometry, lineMaterial(opacity)) : new THREE.Line(geometry, lineMaterial(opacity));
}

function ring(radius: number, opacity = .2) {
  return line(Array.from({ length: 160 }, (_, i) => {
    const a = i / 160 * Math.PI * 2;
    return new THREE.Vector3(Math.cos(a) * radius, 0, Math.sin(a) * radius);
  }), opacity, true);
}

function skeleton(jointGeometry: THREE.SphereGeometry, boneGeometry: THREE.CylinderGeometry, opacity = 1) {
  const group = new THREE.Group();
  const finish = material(opacity);
  const joints = BODY.map((_, i) => {
    const mesh = new THREE.Mesh(jointGeometry, finish);
    mesh.scale.setScalar(i === 10 ? 1.5 : i === 0 || i === 8 ? 1.12 : .8);
    group.add(mesh);
    return mesh;
  });
  const bones = BONES.map(() => {
    const mesh = new THREE.Mesh(boneGeometry, finish);
    group.add(mesh);
    return mesh;
  });
  const axis = new THREE.Vector3(0, 1, 0);
  const direction = new THREE.Vector3();
  function update(points: THREE.Vector3[], masked: Set<number> = new Set()) {
    joints.forEach((joint, i) => { joint.position.copy(points[i]); joint.visible = !masked.has(i); });
    bones.forEach((bone, i) => {
      const [a, b] = BONES[i];
      direction.subVectors(points[b], points[a]);
      bone.position.copy(points[a]).add(points[b]).multiplyScalar(.5);
      bone.scale.y = direction.length();
      bone.quaternion.setFromUnitVectors(axis, direction.normalize());
      bone.visible = !masked.has(a) && !masked.has(b);
    });
  }
  update(pose(.6));
  return { group, update };
}

function alpha(group: THREE.Group, value: number) {
  group.visible = value > .002;
  if (!group.visible) return;
  group.traverse((object) => {
    if (!(object instanceof THREE.Mesh || object instanceof THREE.Line || object instanceof THREE.Points)) return;
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    materials.forEach((item) => {
      if (item.userData.baseOpacity === undefined) item.userData.baseOpacity = item.opacity;
      item.opacity = item.userData.baseOpacity * value;
    });
  });
}

export default function JourneyScene(props: JourneySceneProps) {
  const host = useRef<HTMLDivElement>(null);
  const current = useRef(props);
  const invalidate = useRef<() => void>(() => {});

  useEffect(() => {
    current.current = props;
    invalidate.current();
  }, [props]);

  useEffect(() => {
    const container = host.current;
    if (!container) return;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "low-power" });
    } catch {
      current.current.onUnavailable();
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
    renderer.setClearColor(0x000000, 0);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.35;
    renderer.domElement.setAttribute("aria-hidden", "true");
    renderer.domElement.style.cssText = "display:block;width:100%;height:100%;pointer-events:none";
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(35, 1, .1, 80);
    const world = new THREE.Group();
    scene.add(world);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x323232, 2.2));
    const key = new THREE.DirectionalLight(0xffffff, 4.5);
    key.position.set(-3, 5, 4);
    const rim = new THREE.DirectionalLight(0xcecece, 3);
    rim.position.set(4, .5, -3);
    scene.add(key, rim);

    const groups = Object.fromEntries(STAGES.map((name) => [name, new THREE.Group()])) as Record<JourneyStage, THREE.Group>;
    STAGES.forEach((name) => world.add(groups[name]));
    const jointGeometry = new THREE.SphereGeometry(.062, 12, 8);
    const boneGeometry = new THREE.CylinderGeometry(.017, .022, 1, 8);
    const mainPose = skeleton(jointGeometry, boneGeometry);
    groups.motion.add(mainPose.group);
    mainPose.group.scale.setScalar(1.16);
    const mainPoints = pose(.6);

    // Chronological silhouettes and wrist/ankle trajectories turn motion into a sculpture.
    for (let step = 0; step < 9; step++) {
      const phase = .6 - (step + 1) * .34;
      const points = pose(phase);
      const offset = new THREE.Vector3(-.11 * (step + 1), -.016 * step, -.17 * (step + 1));
      const ghost = new THREE.LineSegments(
        new THREE.BufferGeometry().setFromPoints(BONES.flatMap(([a, b]) => [points[a].clone().add(offset), points[b].clone().add(offset)])),
        lineMaterial(.16 - step * .012),
      );
      groups.motion.add(ghost);
    }
    [3, 6, 13, 16].forEach((joint, index) => {
      const path = Array.from({ length: 150 }, (_, i) => {
        const t = i / 149;
        const p = pose(t * Math.PI * 3)[joint].clone();
        p.x += (t - .5) * 2.4;
        p.z += Math.sin(t * Math.PI * 2) * .65;
        return p;
      });
      groups.motion.add(line(path, index > 1 ? .5 : .24));
      const secondary = line(path.map((p) => p.clone().add(new THREE.Vector3(0, .026, -.025))), .09);
      groups.motion.add(secondary);
    });

    const encoderPose = skeleton(jointGeometry, boneGeometry, .75);
    encoderPose.group.scale.setScalar(.52);
    encoderPose.group.position.set(-1.9, .1, .15);
    groups.encoder.add(encoderPose.group);
    for (let i = 0; i < 5; i++) {
      const box = new THREE.BoxGeometry(1.38, 2.15, .025);
      const plane = new THREE.Mesh(box, new THREE.MeshStandardMaterial({ color: 0xc6c6c6, metalness: .65, roughness: .35, transparent: true, opacity: .08 }));
      plane.position.z = (i - 2) * .28;
      const frame = new THREE.LineSegments(new THREE.EdgesGeometry(box), lineMaterial(i === 2 ? .55 : .2));
      plane.add(frame);
      groups.encoder.add(plane);
    }
    for (let i = 0; i < 8; i++) {
      const y = (i - 3.5) * .17;
      groups.encoder.add(line([new THREE.Vector3(-1.35, y, .1), new THREE.Vector3(-.77, y, .1)], .28));
      groups.encoder.add(line([new THREE.Vector3(.77, y, .1), new THREE.Vector3(1.3, y * .6, .1)], .28));
    }

    const constellation: THREE.Vector3[] = Array.from({ length: 36 }, (_, i) => {
      const family = i % 3;
      const angle = family / 3 * Math.PI * 2 + .35;
      return new THREE.Vector3(Math.cos(angle) * .93 + (noise(i, 2) - .5) * 1.5, Math.sin(angle) * .78 + (noise(i, 3) - .5) * 1.4, (noise(i, 4) - .5) * 1.7);
    });
    const nodeGeometry = new THREE.IcosahedronGeometry(.048, 1);
    const nodeFinish = material(.92, .15);
    constellation.forEach((point, i) => {
      const node = new THREE.Mesh(nodeGeometry, nodeFinish);
      node.position.copy(point);
      node.scale.setScalar(i === 0 ? 1.8 : 1);
      groups.space.add(node);
    });
    const topology = new THREE.LineSegments(new THREE.BufferGeometry(), lineMaterial(.36));
    groups.space.add(topology);
    const focusRing = ring(.3, .42);
    focusRing.rotation.x = Math.PI / 2;
    focusRing.position.copy(constellation[0]);
    groups.space.add(focusRing);
    let recipe = "";
    function updateTopology(next: JourneySceneProps["recipe"]) {
      if (recipe === next) return;
      recipe = next;
      const edges: THREE.Vector3[] = [];
      constellation.forEach((point, i) => {
        if (i === 0) return;
        if (next === "contrastive" && i === 3) edges.push(constellation[0], point);
        if (next === "supcon" && i % 3 === 0) edges.push(constellation[0], point);
        if (next === "contextual" && i < 11) {
          edges.push(constellation[0], point);
          if (i > 1) edges.push(constellation[i - 1], point);
          if (i > 3) edges.push(constellation[3], point);
        }
      });
      topology.geometry.dispose();
      topology.geometry = new THREE.BufferGeometry().setFromPoints(edges);
    }

    const cleanPose = skeleton(jointGeometry, boneGeometry, .62);
    const queryPose = skeleton(jointGeometry, boneGeometry);
    [cleanPose, queryPose].forEach((figure, i) => {
      figure.group.position.x = i === 0 ? -1.13 : 1.13;
      figure.group.scale.setScalar(.83);
      groups.corruption.add(figure.group);
      const pedestal = ring(.68, .3);
      pedestal.position.set(figure.group.position.x, -1.32, 0);
      groups.corruption.add(pedestal);
    });
    const queryPoints = pose(.6);
    const cleanPoints = pose(.6);
    const frameGeometry = new THREE.BoxGeometry(.023, .07, .025);
    const frameFinish = material(.6, 0);
    const referenceFrames = new THREE.InstancedMesh(frameGeometry, frameFinish, 100);
    const queryFrames = new THREE.InstancedMesh(frameGeometry, frameFinish, 100);
    const matrix = new THREE.Matrix4();
    const emptyScale = new THREE.Vector3(0, 0, 0);
    const unitScale = new THREE.Vector3(1, 1, 1);
    const framePosition = new THREE.Vector3();
    const identity = new THREE.Quaternion();
    for (let i = 0; i < 100; i++) {
      framePosition.set((i % 25) * .051 - 1.75, -1.61 - Math.floor(i / 25) * .1, .1);
      referenceFrames.setMatrixAt(i, matrix.compose(framePosition, identity, unitScale));
    }
    groups.corruption.add(referenceFrames, queryFrames);
    const missing = new Set<number>();

    const headGeometry = new THREE.BoxGeometry(.35, .46, .19);
    const headFinish = material(.7, .65);
    const heads: THREE.Group[] = [];
    for (let i = 0; i < 9; i++) {
      const holder = new THREE.Group();
      const body = new THREE.Mesh(headGeometry, headFinish);
      holder.add(body, new THREE.LineSegments(new THREE.EdgesGeometry(headGeometry), lineMaterial(.65)));
      const lock = new THREE.Mesh(new THREE.TorusGeometry(.071, .011, 6, 20, Math.PI), material(.85));
      lock.position.set(0, .026, .111);
      holder.add(lock);
      const lockBase = new THREE.Mesh(new THREE.BoxGeometry(.13, .1, .015), material(.85));
      lockBase.position.set(0, -.03, .115);
      holder.add(lockBase);
      heads.push(holder);
      groups.heads.add(holder);
    }
    [1.25, 1.72, 2.13].forEach((radius, i) => {
      const orbit = ring(radius, .2);
      orbit.rotation.set(.25 + i * .17, 0, .15 + i * .08);
      groups.heads.add(orbit);
    });
    const core = new THREE.Mesh(new THREE.IcosahedronGeometry(.48, 1), new THREE.MeshStandardMaterial({ color: 0x8d8d8d, metalness: .8, roughness: .28, transparent: true, opacity: .6 }));
    core.add(new THREE.LineSegments(new THREE.EdgesGeometry(core.geometry), lineMaterial(.5)));
    groups.heads.add(core);

    // Empty report leaves: a reporting commitment, deliberately containing no invented result.
    for (let i = 0; i < 5; i++) {
      const sheet = new THREE.Group();
      const geometry = new THREE.BoxGeometry(1.65, 2.2, .026);
      sheet.add(new THREE.Mesh(geometry, material(.09, .7)));
      sheet.add(new THREE.LineSegments(new THREE.EdgesGeometry(geometry), lineMaterial(.42)));
      for (let row = 0; row < 7; row++) {
        sheet.add(line([new THREE.Vector3(-.56, .66 - row * .2, .025), new THREE.Vector3(row === 0 ? .14 : .57, .66 - row * .2, .025)], row === 0 ? .8 : .19));
      }
      sheet.position.set((i - 2) * .32, (i - 2) * .065, -(i - 2) * .29);
      sheet.rotation.y = -.22;
      groups.results.add(sheet);
    }

    const targets = STAGES.map((stage) => {
      const positions = new Float32Array(PARTICLES * 3);
      for (let i = 0; i < PARTICLES; i++) {
        const a = noise(i, 7) * Math.PI * 2;
        const y = noise(i, 8) * 2 - 1;
        const r = Math.sqrt(1 - y * y);
        let x = Math.cos(a) * r * 1.65;
        let z = Math.sin(a) * r * 1.65;
        let py = y * 1.65;
        if (stage === "motion") {
          const p = pose(i / PARTICLES * Math.PI * 5)[[3, 6, 13, 16][i % 4]];
          x = p.x + (i / PARTICLES - .5) * 2.8;
          py = p.y + (noise(i, 9) - .5) * .07;
          z = p.z - .7 + Math.sin(i / PARTICLES * Math.PI * 3) * .8;
        } else if (stage === "encoder") {
          x = 1.67 + x * .36;
          py *= .36;
          z *= .36;
        } else if (stage === "space") {
          const p = constellation[i % constellation.length];
          x = p.x + x * .12;
          py = p.y + py * .12;
          z = p.z + z * .12;
        } else if (stage === "corruption") {
          const t = i / PARTICLES * Math.PI * 2;
          x = Math.cos(t) * 2.12;
          py = -1.31 + (noise(i, 8) - .5) * .018;
          z = Math.sin(t) * .74;
        } else if (stage === "heads") {
          x *= .4; py *= .4; z *= .4;
        } else {
          x = (noise(i, 7) - .5) * 1.55;
          py = (noise(i, 8) - .5) * 2.1;
          z = -.9 + noise(i, 9) * .07;
        }
        positions.set([x, py, z], i * 3);
      }
      return positions;
    });
    const particlesGeometry = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(targets[STAGES.indexOf(current.current.stage)]);
    const positionAttribute = new THREE.BufferAttribute(particlePositions, 3).setUsage(THREE.DynamicDrawUsage);
    particlesGeometry.setAttribute("position", positionAttribute);
    const particlesMaterial = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false,
      uniforms: { uSize: { value: 18 }, uOpacity: { value: .65 } },
      vertexShader: "uniform float uSize; void main(){ vec4 p=modelViewMatrix*vec4(position,1.0); gl_PointSize=clamp(uSize/-p.z,1.0,5.0); gl_Position=projectionMatrix*p; }",
      fragmentShader: "uniform float uOpacity; void main(){ float d=length(gl_PointCoord-vec2(.5)); float a=smoothstep(.5,.08,d); gl_FragColor=vec4(vec3(.9),a*uOpacity); }",
    });
    const particles = new THREE.Points(particlesGeometry, particlesMaterial);
    particles.frustumCulled = false;
    world.add(particles);
    const ground = ring(2.7, .1);
    ground.position.y = -1.66;
    world.add(ground);
    const groundInner = ring(2.54, .045);
    groundInner.position.y = -1.66;
    world.add(groundInner);

    let disposed = false;
    let unavailable = false;
    let visible = true;
    let frame = 0;
    let previousTime = 0;
    let elapsed = .6;
    let firstRender = true;
    let angle = .28;
    let targetAngle = .28;
    const weights: number[] = STAGES.map((name) => name === current.current.stage ? 1 : 0);
    let settling = 0;

    function schedule() {
      if (!frame && !disposed && !unavailable && visible && !document.hidden) frame = requestAnimationFrame(render);
    }
    function render(timestamp: number) {
      frame = 0;
      if (disposed || unavailable) return;
      const options = current.current;
      const dt = Math.min((timestamp - (previousTime || timestamp)) / 1000, .04);
      previousTime = timestamp;
      const animate = options.playing && !options.reducedMotion;
      if (animate) elapsed += dt * .54;
      const scrubFrame = !options.playing && options.frame !== undefined ? clamp(Math.round(options.frame), 0, 99) : null;
      const poseTime = scrubFrame === null ? elapsed : scrubFrame / 100 * Math.PI * 2;
      const blend = options.reducedMotion ? 1 : 1 - Math.exp(-dt * 5.5);
      const index = STAGES.indexOf(options.stage);
      const progress = clamp(options.progress, 0, 1);
      let movement = 0;
      weights.forEach((value, i) => {
        weights[i] = THREE.MathUtils.lerp(value, i === index ? 1 : 0, blend);
        movement += Math.abs(weights[i] - (i === index ? 1 : 0));
        alpha(groups[STAGES[i]], weights[i]);
      });
      let particleMovement = 0;
      for (let i = 0; i < particlePositions.length; i++) {
        particlePositions[i] += (targets[index][i] - particlePositions[i]) * blend;
        particleMovement = Math.max(particleMovement, Math.abs(targets[index][i] - particlePositions[i]));
      }
      positionAttribute.needsUpdate = true;
      particlesMaterial.uniforms.uOpacity.value = options.stage === "results" ? .2 : .62;
      pose(poseTime, mainPoints);
      mainPose.update(mainPoints);
      encoderPose.update(mainPoints);
      pose(poseTime, cleanPoints);
      pose(poseTime, queryPoints);
      const severity = clamp(Math.round(options.severity), 0, 3);
      missing.clear();
      if (options.corruption === "joints") MASK_ORDER.slice(0, [0, 3, 6, 8][severity]).forEach((joint) => missing.add(joint));
      if (options.corruption === "jitter") {
        const magnitude = [0, .01, .025, .05][severity] * .88;
        queryPoints.forEach((point, i) => {
          // Fixed Gaussian field reused at every severity; x/y only, matching the tensor stress test.
          const gaussian = Math.sqrt(-2 * Math.log(Math.max(.001, noise(i, 21))));
          point.x += Math.cos(noise(i, 22) * Math.PI * 2) * gaussian * magnitude;
          point.y += Math.sin(noise(i, 22) * Math.PI * 2) * gaussian * magnitude;
        });
      }
      cleanPose.update(cleanPoints);
      queryPose.update(queryPoints, missing);
      const dropped = options.corruption === "frames" ? [0, 10, 25, 40][severity] : 0;
      const start = Math.floor(.46 * (101 - dropped));
      const frameIndex = scrubFrame ?? Math.floor((poseTime % (Math.PI * 2)) / (Math.PI * 2) * 100);
      queryPose.group.visible = dropped === 0 || frameIndex < start || frameIndex >= start + dropped;
      for (let i = 0; i < 100; i++) {
        framePosition.set((i % 25) * .051 + .52, -1.61 - Math.floor(i / 25) * .1, .1);
        queryFrames.setMatrixAt(i, matrix.compose(framePosition, identity, i >= start && i < start + dropped ? emptyScale : unitScale));
      }
      queryFrames.instanceMatrix.needsUpdate = true;
      updateTopology(options.recipe);
      heads.forEach((head, i) => {
        const band = Math.floor(i / 3);
        const a = i % 3 / 3 * Math.PI * 2 + band * .42 + elapsed * .08;
        const radius = [1.25, 1.72, 2.13][band];
        head.position.set(Math.cos(a) * radius, Math.sin(a) * (.25 + band * .15), Math.sin(a) * radius);
        head.rotation.y = -a + Math.PI / 2;
      });
      core.rotation.set(elapsed * .07, elapsed * .12, .2);
      targetAngle = [.28, -.65, 1.02][options.view % 3] + (options.reducedMotion ? 0 : (progress - .5) * .12);
      angle = THREE.MathUtils.lerp(angle, targetAngle, blend);
      const distance = camera.aspect < .85 ? 10.5 : 8.2;
      camera.position.set(Math.sin(angle) * distance, options.reducedMotion ? .85 : .75 + progress * .28, Math.cos(angle) * distance);
      camera.lookAt(0, -.15, 0);
      renderer.render(scene, camera);
      if (firstRender) {
        firstRender = false;
        container?.setAttribute("data-webgl", "ready");
        current.current.onReady();
      }
      settling = movement > .002 || particleMovement > .001 || Math.abs(angle - targetAngle) > .001 ? 0 : settling + 1;
      if (animate || settling < 2) schedule();
    }
    function wake() { settling = 0; schedule(); }
    function resize() {
      const { width, height } = container!.getBoundingClientRect();
      if (width < 1 || height < 1) return;
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      wake();
    }
    function availability() {
      if (document.hidden && frame) { cancelAnimationFrame(frame); frame = 0; }
      previousTime = 0;
      if (!document.hidden) wake();
    }
    function contextLost(event: Event) {
      event.preventDefault();
      unavailable = true;
      cancelAnimationFrame(frame);
      frame = 0;
      container?.setAttribute("data-webgl", "unavailable");
      current.current.onUnavailable();
    }
    const observer = new ResizeObserver(resize);
    observer.observe(container);
    const intersection = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      if (!visible && frame) { cancelAnimationFrame(frame); frame = 0; }
      previousTime = 0;
      if (visible) wake();
    }, { rootMargin: "120px" });
    intersection.observe(container);
    document.addEventListener("visibilitychange", availability);
    renderer.domElement.addEventListener("webglcontextlost", contextLost);
    invalidate.current = wake;
    resize();

    return () => {
      disposed = true;
      invalidate.current = () => {};
      cancelAnimationFrame(frame);
      observer.disconnect();
      intersection.disconnect();
      document.removeEventListener("visibilitychange", availability);
      renderer.domElement.removeEventListener("webglcontextlost", contextLost);
      const geometries = new Set<THREE.BufferGeometry>();
      const materials = new Set<THREE.Material>();
      scene.traverse((object) => {
        if (!(object instanceof THREE.Mesh || object instanceof THREE.Line || object instanceof THREE.Points)) return;
        geometries.add(object.geometry);
        (Array.isArray(object.material) ? object.material : [object.material]).forEach((item) => materials.add(item));
      });
      geometries.forEach((geometry) => geometry.dispose());
      materials.forEach((item) => item.dispose());
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);

  return <div ref={host} className="journey-webgl" data-webgl="loading" aria-hidden="true" style={{ width: "100%", height: "100%", pointerEvents: "none" }} />;
}
