# Copyright (c) 2012, Michal Zielinski <michal@zielinscy.org.pl>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
#     * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
# 
#     * Redistributions in binary form must reproduce the above
#     copyright notice, this list of conditions and the following
#     disclaimer in the documentation and/or other materials provided
#     with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import g3d
from g3d import Vector2, Vector3, Quaternion
from g3d.model.reader import read

import abc

class Model:
    '''
    Model represents an object - it consists of:
    - parts (immutable g3d.TriangleObjects),
    - animations (g3d.model.Animation - describes transformations of parts).
    Parts are grouped (using g3d.Container) to make applying transformations easier.
    '''
    def __init__(self):
        self.root = g3d.Container()
        self.animations = {}
        self.objects = {}

    def play(self, animator, name):
        animator.play(self.animations[name])
        
    def clone(self):
        pass # TODO

class Animator:
    '''
    Manages playing and stopping animations. Needs to be attached to timer with .install(timer)
    '''
    def __init__(self):
        self.animations = set()

    def tick(self, time):
        for anim in list(self.animations):
            if not anim.tick(time):
                self.animations.remove(anim)

    def play(self, anim):
        anim.init()
        self.animations.add(anim)

    def stop(self, anim):
        self.animations.remove(anim)

    def install(self, timer):
        timer.add_ticker(self.tick)

class Animation:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def init(self):
        ''' Called when animation is started.
        If animation is started more than one time this method will
        be called more than one time. '''

    @abc.abstractmethod
    def tick(self, time):
        ''' Called on each game tick when animation is running.
        If this method returns false value animation will be stopped. '''
    
class AnimationGroup(Animation):
    def __init__(self):
        self.anims = []
    
    def add(self, start, animation):
        ' Adds animation to group - cannot be called when animation is running. '
        self.anims.append((start, animation))

    def init(self):
        self.anims.sort()
        self.time = 0
        self.running = []
        self.next_child = 0

    def tick(self, time):
        self.time += time

        anything_left = False
        for anim in list(self.running):
            if anim.tick(time):
                anything_left = True
            else:
                self.running.remove(anim)
        
        while self.next_child < len(self.anims):
            start_at, anim = self.anims[self.next_child]
            if start_at < self.time:
                anything_left = True
                self.running.append(anim)
                anim.init()
                anim.tick(self.time - start_at)
                self.next_child += 1
            else:
                break

        if not anything_left and self.next_child == len(self.anims):
            return False
        else:
            return True
    
class InterpolateRotation(Animation):
    def __init__(self, object, dest_rotation, speed=None, time=None):
        ''' speed in radians '''
        assert isinstance(dest_rotation, Quaternion)
        assert (speed or time) and not (speed and time), \
            'Exactly one of [speed, time] have to be given'
        self.req_speed = speed
        self.req_time = time
        self.object = object
        self.dest_rotation = dest_rotation

    def init(self):
        self.start_rotation = self.object.rotation
        self.total_time = self._compute_time()
        self.current_time = 0

    def _compute_time(self):
        if self.req_time:
            return self.req_time
        else:
            angle = Quaternion.angle_between(self.start_rotation, self.dest_rotation)
            return angle / self.req_speed
        
    def tick(self, time):
        self.current_time += time
        fraction = self.current_time / self.total_time # part of animation done
        if fraction > 1:
            fraction = 1
        current_rotation = Quaternion.new_interpolate(self.start_rotation,
                                                      self.dest_rotation,
                                                      fraction)
        self.object.rotation = current_rotation
        return fraction != 1 # continue animation iff it is not completed
    
